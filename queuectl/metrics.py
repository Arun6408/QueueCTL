"""Metrics collection and statistics."""

import time
from datetime import datetime
from typing import Dict, Any, List
from queuectl.storage import Storage
from queuectl.models import JobState


class Metrics:
    """Collect and provide metrics about job execution."""
    
    def __init__(self, storage: Storage):
        """Initialize metrics collector."""
        self.storage = storage
        self._execution_times: Dict[str, float] = {}  # job_id -> execution_time
        self._start_times: Dict[str, float] = {}  # job_id -> start_time
    
    def record_job_start(self, job_id: str):
        """Record when a job starts processing."""
        self._start_times[job_id] = time.time()
    
    def record_job_end(self, job_id: str, success: bool):
        """Record when a job finishes processing."""
        if job_id in self._start_times:
            execution_time = time.time() - self._start_times[job_id]
            self._execution_times[job_id] = execution_time
            del self._start_times[job_id]
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        if not self._execution_times:
            return {
                "total_executions": 0,
                "avg_execution_time": 0,
                "min_execution_time": 0,
                "max_execution_time": 0,
            }
        
        times = list(self._execution_times.values())
        return {
            "total_executions": len(times),
            "avg_execution_time": sum(times) / len(times),
            "min_execution_time": min(times),
            "max_execution_time": max(times),
        }
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics combined."""
        stats = self.storage.get_stats()
        exec_stats = self.get_execution_stats()
        
        return {
            "job_stats": stats,
            "execution_stats": exec_stats,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    
    def reset(self):
        """Reset metrics."""
        self._execution_times.clear()
        self._start_times.clear()

