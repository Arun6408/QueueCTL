# QueueCTL Architecture

## Overview

QueueCTL is a CLI-based background job queue system built with Python. It provides a robust, production-ready solution for managing background jobs with automatic retries, Dead Letter Queue (DLQ), and comprehensive monitoring.

## System Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI Layer                             │
│  (queuectl/cli.py) - Click-based command interface          │
└───────────────────────┬─────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
┌───────▼──────┐ ┌─────▼──────┐ ┌─────▼──────────┐
│   Storage    │ │  Scheduler  │ │ Worker Manager │
│  (SQLite)    │ │             │ │                │
└───────┬──────┘ └─────┬───────┘ └─────┬──────────┘
        │              │               │
        └──────────────┼───────────────┘
                       │
              ┌────────▼────────┐
              │  Worker Threads │
              │  (Job Execution) │
              └─────────────────┘
```

## Core Components

### 1. Models (`queuectl/models.py`)

**Job Model**: Represents a background job with:
- Identity: `id` (unique identifier)
- Execution: `command` (shell command to run)
- State: `pending`, `processing`, `completed`, `failed`, `dead`
- Retry: `attempts`, `max_retries`, `next_retry_at`
- Metadata: `priority`, `run_at`, `timeout`, `output`, `error`
- Timestamps: `created_at`, `updated_at`

**JobState Enum**: Defines all possible job states

### 2. Storage (`queuectl/storage.py`)

**SQLite-based persistence** with:
- Thread-safe operations using `threading.RLock`
- Atomic job locking via database updates
- Efficient queries with indexes on `state`, `priority`, `run_at`, `next_retry_at`
- Methods:
  - `add_job()`: Add new job
  - `get_job()`: Retrieve job by ID
  - `update_job()`: Update job state/data
  - `get_next_pending_job()`: Get highest priority pending job
  - `get_retryable_jobs()`: Get jobs ready for retry
  - `reset_retryable_job_to_pending()`: Atomic reset for retries
  - `list_jobs()`: List jobs with filters
  - `get_dlq_jobs()`: Get Dead Letter Queue jobs
  - `get_stats()`: Get job statistics

### 3. Scheduler (`queuectl/scheduler.py`)

**Job execution and retry logic**:
- `JobExecutor`: Executes shell commands with timeout
- `Scheduler`: Manages job lifecycle
  - `process_job()`: Execute job and handle success/failure
  - `schedule_retry()`: Calculate exponential backoff and schedule
  - `move_to_dlq()`: Move permanently failed jobs to DLQ
  - `get_next_job()`: Get next job ready for processing

**Exponential Backoff**: `delay = base ^ attempts` seconds

### 4. Worker (`queuectl/worker.py`)

**Worker management**:
- `Worker`: Single worker thread
  - Polls for jobs
  - Atomically locks jobs (database-level)
  - Processes jobs via scheduler
  - Graceful shutdown support
  
- `WorkerManager`: Manages multiple workers
  - Start/stop workers
  - Signal handling for graceful shutdown
  - Worker status tracking

**Locking Mechanism**: 
- Database-level atomic updates prevent race conditions
- `UPDATE jobs SET state = 'processing' WHERE id = ? AND state = 'pending'`
- Only one worker can successfully claim a job

### 5. Configuration (`queuectl/config.py`)

**File-based configuration**:
- JSON config file in `~/.queuectl/config.json`
- Default values for all settings
- CLI commands to get/set configuration
- Persists across restarts

### 6. CLI (`queuectl/cli.py`)

**Click-based command interface**:
- `enqueue`: Add new jobs
- `worker start/stop`: Manage workers
- `status`: System overview
- `list`: List jobs with filters
- `dlq list/retry`: Dead Letter Queue management
- `config set/show`: Configuration management
- `dashboard`: Start web dashboard

### 7. Metrics (`queuectl/metrics.py`)

**Execution statistics**:
- Track job execution times
- Calculate averages, min, max
- Combined with storage stats for comprehensive metrics

### 8. Web Dashboard (`queuectl/web_dashboard.py`)

**Flask-based monitoring**:
- Real-time job statistics
- Worker status
- Recent jobs list
- Auto-refresh every 5 seconds
- RESTful API endpoints

## Data Flow

### Job Enqueue Flow

```
User → CLI → Storage.add_job() → SQLite
                    ↓
            Job state: pending
```

### Job Processing Flow

```
Worker Loop:
  1. Poll Storage.get_next_job()
  2. Try atomic lock (UPDATE state pending → processing)
  3. If locked successfully:
     - Execute job via Scheduler
     - Update state (completed/failed)
     - If failed: schedule retry or move to DLQ
  4. Repeat
```

### Retry Flow

```
Job fails → attempts++
  ↓
If attempts < max_retries:
  Calculate backoff delay = base ^ attempts
  Set next_retry_at = now + delay
  State: failed
  ↓
When next_retry_at <= now:
  Reset to pending
  Worker picks up
  ↓
Else (attempts >= max_retries):
  Move to DLQ (state: dead)
```

## Concurrency Model

### Thread Safety

1. **Storage Layer**: Uses `threading.RLock()` for all database operations
2. **Job Locking**: Atomic SQL UPDATE prevents duplicate processing
3. **Worker Isolation**: Each worker runs in separate thread
4. **No Shared State**: Workers communicate only through database

### Race Condition Prevention

- **Job Claiming**: Atomic UPDATE with WHERE clause ensures only one worker claims a job
- **Retry Reset**: Atomic UPDATE prevents multiple workers resetting same retryable job
- **State Transitions**: All state changes are atomic database operations

## Persistence Strategy

### SQLite Database

**Schema**:
```sql
CREATE TABLE jobs (
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
);

CREATE INDEX idx_state ON jobs(state);
CREATE INDEX idx_priority ON jobs(priority DESC);
CREATE INDEX idx_run_at ON jobs(run_at);
CREATE INDEX idx_next_retry_at ON jobs(next_retry_at);
```

**Benefits**:
- Zero configuration
- File-based (portable)
- ACID transactions
- Good performance for moderate workloads
- Built-in Python support

## Design Patterns

### 1. Repository Pattern
- Storage layer abstracts database operations
- Clean separation between business logic and persistence

### 2. Strategy Pattern
- Different execution strategies (timeout, retry, DLQ)
- Configurable via configuration

### 3. Observer Pattern (implicit)
- Metrics collection observes job execution
- Web dashboard observes system state

### 4. Factory Pattern
- Job creation from JSON
- Worker creation with configuration

## Error Handling

### Job Execution Errors
- Captured via subprocess stderr
- Stored in job.error field
- Trigger retry mechanism

### Timeout Handling
- Process group created for each job
- Killed on timeout
- Error recorded

### Database Errors
- Locking prevents concurrent access issues
- Transactions ensure consistency
- Error logging for debugging

## Scalability Considerations

### Current Limitations
- Single-machine deployment
- SQLite may bottleneck at very high throughput (>1000 jobs/sec)
- Thread-based workers (I/O-bound tasks)

### Potential Improvements
- Distributed workers (Redis/RabbitMQ backend)
- Process-based workers for CPU-bound tasks
- Connection pooling for database
- Async job execution
- Job batching

## Security Considerations

### Current Implementation
- Jobs execute with same privileges as QueueCTL process
- No input sanitization beyond JSON validation
- Web dashboard binds to all interfaces

### Recommendations for Production
- Run workers with limited privileges
- Validate and sanitize job commands
- Restrict web dashboard to localhost
- Add authentication for web dashboard
- Rate limiting for job enqueue
- Command whitelist/blacklist

## Testing Strategy

### Test Scenarios (`test_scenarios.py`)
1. Basic job completion
2. Failed job retry and DLQ
3. Multiple workers (no overlap)
4. Invalid command handling
5. Persistence across restarts

### Manual Testing
- Demo scripts (`demo.sh`, `demo.bat`)
- CLI command validation
- Web dashboard functionality

## Performance Metrics

### Typical Performance
- Job enqueue: < 10ms
- Job processing: Depends on command
- Worker polling: Configurable (default 1s)
- Database queries: < 5ms (with indexes)

### Bottlenecks
- SQLite write contention (mitigated by locking)
- Worker polling frequency
- Job execution time (external dependency)

## Future Enhancements

1. **Distributed Architecture**
   - Redis/RabbitMQ backend
   - Multi-node deployment
   - Job routing

2. **Advanced Features**
   - Job dependencies
   - Job cancellation
   - Job priorities (enhanced)
   - Job groups/batches

3. **Monitoring**
   - Prometheus metrics
   - Distributed tracing
   - Performance profiling

4. **Reliability**
   - Job checkpointing
   - Automatic recovery
   - Health checks

---

This architecture provides a solid foundation for a production-grade job queue system while maintaining simplicity and ease of use.

