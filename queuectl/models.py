"""Job model and state definitions."""

from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
import json


class JobState(Enum):
    """Job state enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD = "dead"


@dataclass
class Job:
    """Job model representing a background task."""
    id: str
    command: str
    state: str = JobState.PENDING.value
    attempts: int = 0
    max_retries: int = 3
    created_at: str = None
    updated_at: str = None
    priority: int = 0  # Higher number = higher priority
    run_at: Optional[str] = None  # ISO format datetime for scheduled jobs
    timeout: Optional[int] = None  # Timeout in seconds
    output: Optional[str] = None  # Job output/error logs
    error: Optional[str] = None  # Error message if failed
    next_retry_at: Optional[str] = None  # When to retry (for exponential backoff)
    
    def __post_init__(self):
        """Initialize timestamps if not provided."""
        now = datetime.utcnow().isoformat() + "Z"
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert job to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Job":
        """Create job from dictionary."""
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> "Job":
        """Create job from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def update_state(self, new_state: JobState, error: Optional[str] = None):
        """Update job state and timestamp."""
        self.state = new_state.value
        self.updated_at = datetime.utcnow().isoformat() + "Z"
        if error:
            self.error = error
    
    def increment_attempts(self):
        """Increment retry attempts."""
        self.attempts += 1
        self.updated_at = datetime.utcnow().isoformat() + "Z"
    
    def should_retry(self) -> bool:
        """Check if job should be retried."""
        return (
            self.state == JobState.FAILED.value and
            self.attempts < self.max_retries
        )
    
    def should_move_to_dlq(self) -> bool:
        """Check if job should be moved to DLQ."""
        return (
            self.state == JobState.FAILED.value and
            self.attempts >= self.max_retries
        )
    
    def is_ready_to_run(self) -> bool:
        """Check if job is ready to be executed (not scheduled for future)."""
        if self.run_at is None:
            return True
        
        from dateutil.parser import parse
        run_time = parse(self.run_at)
        return datetime.utcnow() >= run_time.replace(tzinfo=None)

