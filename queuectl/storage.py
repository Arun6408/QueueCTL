"""Persistent storage layer using SQLite."""

import sqlite3
import json
import threading
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from queuectl.models import Job, JobState


class Storage:
    """Thread-safe SQLite storage for jobs."""
    
    def __init__(self, db_path: str = "queuectl.db"):
        """Initialize storage with database path."""
        self.db_path = Path(db_path)
        self._lock = threading.RLock()
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        with self._lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    command TEXT NOT NULL,
                    state TEXT NOT NULL,
                    attempts INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3,
                    priority INTEGER DEFAULT 0,
                    run_at TEXT,
                    timeout INTEGER,
                    output TEXT,
                    error TEXT,
                    next_retry_at TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_state ON jobs(state)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_priority ON jobs(priority DESC)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_run_at ON jobs(run_at)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_next_retry_at ON jobs(next_retry_at)
            """)
            
            conn.commit()
            conn.close()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _row_to_job(self, row: sqlite3.Row) -> Job:
        """Convert database row to Job object."""
        data = dict(row)
        return Job.from_dict(data)
    
    def add_job(self, job: Job) -> bool:
        """Add a new job to storage."""
        with self._lock:
            conn = self._get_connection()
            try:
                conn.execute("""
                    INSERT INTO jobs (
                        id, command, state, attempts, max_retries, priority,
                        run_at, timeout, output, error, next_retry_at,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    job.id, job.command, job.state, job.attempts, job.max_retries,
                    job.priority, job.run_at, job.timeout, job.output, job.error,
                    job.next_retry_at, job.created_at, job.updated_at
                ))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False  # Job ID already exists
            finally:
                conn.close()
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        with self._lock:
            conn = self._get_connection()
            try:
                row = conn.execute(
                    "SELECT * FROM jobs WHERE id = ?", (job_id,)
                ).fetchone()
                return self._row_to_job(row) if row else None
            finally:
                conn.close()
    
    def update_job(self, job: Job) -> bool:
        """Update existing job."""
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.execute("""
                    UPDATE jobs SET
                        command = ?, state = ?, attempts = ?, max_retries = ?,
                        priority = ?, run_at = ?, timeout = ?, output = ?,
                        error = ?, next_retry_at = ?, updated_at = ?
                    WHERE id = ?
                """, (
                    job.command, job.state, job.attempts, job.max_retries,
                    job.priority, job.run_at, job.timeout, job.output,
                    job.error, job.next_retry_at, job.updated_at, job.id
                ))
                conn.commit()
                return cursor.rowcount > 0
            finally:
                conn.close()
    
    def get_next_pending_job(self) -> Optional[Job]:
        """Get next pending job (highest priority, oldest first)."""
        with self._lock:
            conn = self._get_connection()
            try:
                # Get pending jobs that are ready to run (not scheduled for future)
                now = datetime.utcnow().isoformat() + "Z"
                row = conn.execute("""
                    SELECT * FROM jobs
                    WHERE state = ? AND (run_at IS NULL OR run_at <= ?)
                    ORDER BY priority DESC, created_at ASC
                    LIMIT 1
                """, (JobState.PENDING.value, now)).fetchone()
                return self._row_to_job(row) if row else None
            finally:
                conn.close()
    
    def get_retryable_jobs(self) -> List[Job]:
        """Get jobs that are ready to retry."""
        with self._lock:
            conn = self._get_connection()
            try:
                now = datetime.utcnow().isoformat() + "Z"
                rows = conn.execute("""
                    SELECT * FROM jobs
                    WHERE state = ? AND next_retry_at IS NOT NULL AND next_retry_at <= ?
                    ORDER BY next_retry_at ASC
                """, (JobState.FAILED.value, now)).fetchall()
                return [self._row_to_job(row) for row in rows]
            finally:
                conn.close()
    
    def reset_retryable_job_to_pending(self, job_id: str) -> bool:
        """Atomically reset a retryable job to pending state."""
        with self._lock:
            conn = self._get_connection()
            try:
                now = datetime.utcnow().isoformat() + "Z"
                cursor = conn.execute("""
                    UPDATE jobs
                    SET state = ?, next_retry_at = NULL, updated_at = ?
                    WHERE id = ? AND state = ? AND next_retry_at IS NOT NULL AND next_retry_at <= ?
                """, (JobState.PENDING.value, now, job_id, JobState.FAILED.value, now))
                conn.commit()
                return cursor.rowcount > 0
            finally:
                conn.close()
    
    def list_jobs(self, state: Optional[str] = None, limit: int = 100) -> List[Job]:
        """List jobs, optionally filtered by state."""
        with self._lock:
            conn = self._get_connection()
            try:
                if state:
                    rows = conn.execute("""
                        SELECT * FROM jobs
                        WHERE state = ?
                        ORDER BY created_at DESC
                        LIMIT ?
                    """, (state, limit)).fetchall()
                else:
                    rows = conn.execute("""
                        SELECT * FROM jobs
                        ORDER BY created_at DESC
                        LIMIT ?
                    """, (limit,)).fetchall()
                return [self._row_to_job(row) for row in rows]
            finally:
                conn.close()
    
    def get_dlq_jobs(self) -> List[Job]:
        """Get all jobs in Dead Letter Queue."""
        return self.list_jobs(state=JobState.DEAD.value)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about jobs."""
        with self._lock:
            conn = self._get_connection()
            try:
                stats = {}
                for state in JobState:
                    count = conn.execute(
                        "SELECT COUNT(*) FROM jobs WHERE state = ?",
                        (state.value,)
                    ).fetchone()[0]
                    stats[state.value] = count
                
                total = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
                stats["total"] = total
                
                return stats
            finally:
                conn.close()
    
    def delete_job(self, job_id: str) -> bool:
        """Delete a job."""
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
                conn.commit()
                return cursor.rowcount > 0
            finally:
                conn.close()
    
    def reset_job_from_dlq(self, job_id: str) -> Optional[Job]:
        """Reset a DLQ job back to pending state."""
        with self._lock:
            job = self.get_job(job_id)
            if job and job.state == JobState.DEAD.value:
                job.state = JobState.PENDING.value
                job.attempts = 0
                job.error = None
                job.next_retry_at = None
                job.updated_at = datetime.utcnow().isoformat() + "Z"
                self.update_job(job)
                return job
            return None

