"""Worker process management with locking and graceful shutdown."""

import threading
import time
import signal
import sys
import os
from pathlib import Path
from typing import Optional, List
from queuectl.storage import Storage
from queuectl.scheduler import Scheduler
from queuectl.config import Config
from queuectl.models import JobState


class Worker:
    """Single worker thread that processes jobs."""
    
    def __init__(self, worker_id: int, storage: Storage, scheduler: Scheduler, config: Config):
        """Initialize worker."""
        self.worker_id = worker_id
        self.storage = storage
        self.scheduler = scheduler
        self.config = config
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._current_job: Optional[str] = None
        self._lock_file = Path(f".queuectl_worker_{worker_id}.lock")
    
    def _acquire_job_lock(self, job_id: str) -> bool:
        """Try to acquire lock for a job using database-level atomic update."""
        # Use atomic database update to claim the job
        # Only update if state is still pending (prevents race conditions)
        conn = self.storage._get_connection()
        try:
            cursor = conn.execute("""
                UPDATE jobs 
                SET state = ? 
                WHERE id = ? AND state = ?
            """, (JobState.PROCESSING.value, job_id, JobState.PENDING.value))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def _release_job_lock(self, job_id: str):
        """Release lock for a job (no-op, handled by state updates)."""
        pass
    
    def _work_loop(self):
        """Main worker loop."""
        poll_interval = self.config.get("worker_poll_interval", 1)
        
        while self._running:
            try:
                # Get next job
                job = self.scheduler.get_next_job()
                
                if job is None:
                    # No jobs available, wait and retry
                    time.sleep(poll_interval)
                    continue
                
                # Try to acquire lock for this job (atomic database update)
                if not self._acquire_job_lock(job.id):
                    # Another worker claimed this job, try next
                    time.sleep(0.1)
                    continue
                
                # Reload job to get latest state (now should be PROCESSING)
                job = self.storage.get_job(job.id)
                if not job:
                    continue
                
                try:
                    self._current_job = job.id
                    # Process the job
                    self.scheduler.process_job(job)
                finally:
                    self._current_job = None
                
            except Exception as e:
                # Log error but continue working
                print(f"Worker {self.worker_id} error: {e}", file=sys.stderr)
                time.sleep(poll_interval)
    
    def start(self):
        """Start worker thread."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._work_loop, daemon=False)
        self._thread.start()
        
        # Create lock file
        self._lock_file.touch()
    
    def stop(self, timeout: float = 10.0):
        """Stop worker gracefully, waiting for current job to finish."""
        if not self._running:
            return
        
        self._running = False
        
        # Wait for current job to finish
        if self._thread:
            start_time = time.time()
            while self._thread.is_alive() and (time.time() - start_time) < timeout:
                if self._current_job is None:
                    # No current job, can exit immediately
                    break
                time.sleep(0.1)
            
            if self._thread.is_alive():
                # Force stop if timeout exceeded
                print(f"Worker {self.worker_id} force stopped after timeout", file=sys.stderr)
        
        # Remove lock file
        if self._lock_file.exists():
            self._lock_file.unlink()
    
    def is_running(self) -> bool:
        """Check if worker is running."""
        return self._running and self._thread is not None and self._thread.is_alive()
    
    def get_current_job(self) -> Optional[str]:
        """Get ID of currently processing job."""
        return self._current_job


class WorkerManager:
    """Manages multiple worker instances."""
    
    def __init__(self, storage: Storage, scheduler: Scheduler, config: Config):
        """Initialize worker manager."""
        self.storage = storage
        self.scheduler = scheduler
        self.config = config
        self._workers: List[Worker] = []
        self._pid_file = Path(".queuectl_workers.pid")
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            self.stop_all()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def start_workers(self, count: int = 1):
        """Start multiple workers."""
        # Stop existing workers first
        self.stop_all()
        
        # Create new workers
        for i in range(count):
            worker = Worker(i + 1, self.storage, self.scheduler, self.config)
            worker.start()
            self._workers.append(worker)
        
        # Save PID file
        self._pid_file.write_text(str(os.getpid()))
        print(f"Started {count} worker(s)")
    
    def stop_all(self, timeout: float = 10.0):
        """Stop all workers gracefully."""
        for worker in self._workers:
            worker.stop(timeout)
        self._workers.clear()
        
        # Remove PID file
        if self._pid_file.exists():
            self._pid_file.unlink()
        
        print("All workers stopped")
    
    def get_active_workers(self) -> List[Worker]:
        """Get list of active workers."""
        return [w for w in self._workers if w.is_running()]
    
    def get_worker_count(self) -> int:
        """Get number of active workers."""
        return len(self.get_active_workers())
    
    def get_worker_status(self) -> List[dict]:
        """Get status of all workers."""
        status = []
        for worker in self._workers:
            status.append({
                "id": worker.worker_id,
                "running": worker.is_running(),
                "current_job": worker.get_current_job(),
            })
        return status

