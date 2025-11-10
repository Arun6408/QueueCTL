"""Job scheduler with retry logic and exponential backoff."""

import subprocess
import signal
import threading
import time
from datetime import datetime, timedelta
from typing import Optional, Tuple
from dateutil.parser import parse
from queuectl.models import Job, JobState
from queuectl.storage import Storage
from queuectl.config import Config


class JobExecutor:
    """Executes jobs with timeout and output capture."""
    
    def __init__(self, timeout: Optional[int] = None):
        """Initialize executor with optional timeout."""
        self.timeout = timeout
    
    def execute(self, job: Job) -> Tuple[bool, str, Optional[str]]:
        """
        Execute a job command.
        
        Returns:
            (success, output, error) tuple
        """
        try:
            # Execute command with timeout
            process = subprocess.Popen(
                job.command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                start_new_session=True  # Create new process group
            )
            
            timeout = job.timeout or self.timeout
            try:
                stdout, stderr = process.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                # Kill the process group
                try:
                    process.kill()
                    process.wait()
                except:
                    pass
                return False, "", f"Job timed out after {timeout} seconds"
            
            output = stdout + stderr
            success = process.returncode == 0
            
            if not success and not stderr:
                error_msg = f"Command failed with exit code {process.returncode}"
            else:
                error_msg = stderr if stderr else None
            
            return success, output, error_msg
            
        except Exception as e:
            return False, "", str(e)


class Scheduler:
    """Manages job scheduling, retries, and exponential backoff."""
    
    def __init__(self, storage: Storage, config: Config):
        """Initialize scheduler."""
        self.storage = storage
        self.config = config
        self.executor = JobExecutor(timeout=config.get("default_timeout"))
        self._running = False
        self._thread: Optional[threading.Thread] = None
    
    def calculate_retry_delay(self, attempts: int) -> int:
        """Calculate exponential backoff delay in seconds."""
        base = self.config.get("backoff_base", 2)
        return int(base ** attempts)
    
    def schedule_retry(self, job: Job):
        """Schedule a job for retry with exponential backoff."""
        delay = self.calculate_retry_delay(job.attempts)
        retry_time = datetime.utcnow() + timedelta(seconds=delay)
        job.next_retry_at = retry_time.isoformat() + "Z"
        job.update_state(JobState.FAILED)
        self.storage.update_job(job)
    
    def move_to_dlq(self, job: Job, error: str):
        """Move job to Dead Letter Queue."""
        job.update_state(JobState.DEAD, error=error)
        job.next_retry_at = None
        self.storage.update_job(job)
    
    def process_job(self, job: Job) -> bool:
        """
        Process a single job.
        
        Note: Job state should already be PROCESSING (set by worker lock acquisition)
        
        Returns:
            True if job was successfully processed, False otherwise
        """
        # Reload job to ensure we have latest state
        job = self.storage.get_job(job.id)
        if not job:
            return False
        
        # Ensure state is processing (should be set by worker lock)
        if job.state != JobState.PROCESSING.value:
            job.update_state(JobState.PROCESSING)
            self.storage.update_job(job)
        
        # Execute job
        success, output, error = self.executor.execute(job)
        
        # Update job with output
        job.output = output
        
        if success:
            # Job completed successfully
            job.update_state(JobState.COMPLETED)
            self.storage.update_job(job)
            return True
        else:
            # Job failed
            job.increment_attempts()
            
            if job.should_retry():
                # Schedule retry with exponential backoff
                self.schedule_retry(job)
            elif job.should_move_to_dlq():
                # Move to DLQ
                self.move_to_dlq(job, error or "Max retries exceeded")
            else:
                # Shouldn't happen, but handle gracefully
                job.update_state(JobState.FAILED, error=error)
                self.storage.update_job(job)
            
            return False
    
    def get_next_job(self) -> Optional[Job]:
        """Get next job ready to be processed (returns job but doesn't lock it)."""
        # First, check for retryable jobs
        retryable_jobs = self.storage.get_retryable_jobs()
        if retryable_jobs:
            # Try to atomically reset the first retryable job to pending
            job = retryable_jobs[0]
            if self.storage.reset_retryable_job_to_pending(job.id):
                # Successfully reset, reload and return
                return self.storage.get_job(job.id)
            # Another worker reset it, try next job or fall through
        
        # Then check for pending jobs
        return self.storage.get_next_pending_job()

