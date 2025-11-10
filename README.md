# QueueCTL - CLI-based Background Job Queue System

A production-grade, CLI-based background job queue system with worker processes, automatic retries with exponential backoff, Dead Letter Queue (DLQ), and comprehensive monitoring capabilities.

## 🎯 Features

### Core Features
- ✅ **Job Management**: Enqueue, list, and manage background jobs
- ✅ **Worker System**: Multiple parallel workers with database-level locking
- ✅ **Automatic Retries**: Exponential backoff retry mechanism
- ✅ **Dead Letter Queue**: Permanent storage for failed jobs
- ✅ **Persistent Storage**: SQLite-based persistence across restarts
- ✅ **Graceful Shutdown**: Workers finish current jobs before stopping
- ✅ **Configuration Management**: CLI-based configuration

### Extra Features
- ✅ **Job Timeout**: Configurable timeout per job
- ✅ **Priority Queues**: Higher priority jobs processed first
- ✅ **Scheduled Jobs**: Execute jobs at specific times (`run_at`)
- ✅ **Job Output Logging**: Capture and store job output/errors
- ✅ **Execution Metrics**: Track execution times and statistics
- ✅ **Web Dashboard**: Real-time monitoring dashboard (Flask-based)

## 🎬 Demo Video

A working CLI demo video is available:
- [Demo Video Link](https://drive.google.com/your-demo-video-link)

The demo showcases:
- Enqueuing jobs
- Starting workers
- Monitoring job execution
- Retry mechanism
- Dead Letter Queue
- Web dashboard

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. **Clone the repository:**
```bash
git clone <repository-url>
cd FLAM_proje
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Install QueueCTL:**
```bash
pip install -e .
```

4. **Verify installation:**
```bash
queuectl --version
```

## 🚀 Quick Start

### 1. Enqueue a Job

```cmd
queuectl enqueue "{""id"":""job1"",""command"":""echo Hello World""}"
```

#### Windows quoting guide (CMD, PowerShell, Bash)

- **Git Bash / WSL / macOS/Linux (bash/zsh):**

```bash
queuectl enqueue '{"id":"job1","command":"sleep 2"}'
```

- **PowerShell:** (either of the following works)

```powershell
# Recommended
queuectl enqueue '{"id":"job1","command":"timeout /t 2 >nul"}'

# If you see “Invalid JSON format”, use explicit escaping:
queuectl enqueue "{`"id`":`"job1`",`"command`":`"timeout /t 2 >nul`"}"

# Or assign to a variable (most reliable):
$json = '{"id":"job1","command":"timeout /t 2 >nul"}'
queuectl enqueue $json
```

- **Windows CMD:**

```cmd
queuectl enqueue "{""id"":""job1"",""command"":""timeout /t 2 >nul""}"
```

### 2. Start Workers

```cmd
queuectl worker start --count 3
```

### 3. Check Status

```cmd
queuectl status
```

### 4. View Jobs

```cmd
queuectl list
queuectl list --state pending
```

### 5. Monitor with Web Dashboard

```cmd
queuectl dashboard
# Open http://localhost:8080 in your browser
```

## 💻 CLI Commands

### Job Management

| Command | Description | Example |
|---------|-------------|---------|
| `queuectl enqueue <json>` | Enqueue a new job | `queuectl enqueue "{""id"":""job1"",""command"":""timeout /t 2 >nul""}"` |
| `queuectl list [--state <state>]` | List jobs (optionally filtered) | `queuectl list --state pending` |
| `queuectl status` | Show system status and statistics | `queuectl status` |

### Worker Management

| Command | Description | Example |
|---------|-------------|---------|
| `queuectl worker start [--count N]` | Start worker processes | `queuectl worker start --count 3` |
| `queuectl worker stop` | Stop all workers gracefully | `queuectl worker stop` |

### Dead Letter Queue

| Command | Description | Example |
|---------|-------------|---------|
| `queuectl dlq list` | List all DLQ jobs | `queuectl dlq list` |
| `queuectl dlq retry <job_id>` | Reset a DLQ job for retry | `queuectl dlq retry job1` |

### Configuration

| Command | Description | Example |
|---------|-------------|---------|
| `queuectl config set <key> <value>` | Set configuration | `queuectl config set max-retries 5` |
| `queuectl config show` | Show current configuration | `queuectl config show` |

### Web Dashboard

| Command | Description | Example |
|---------|-------------|---------|
| `queuectl dashboard [--port N]` | Start web dashboard | `queuectl dashboard --port 8080` |

## 📋 Job Specification

Each job is defined as a JSON object with the following fields:

```json
{
  "id": "unique-job-id",           // Required: Unique identifier
  "command": "echo 'Hello World'", // Required: Shell command to execute
  "max_retries": 3,                // Optional: Max retry attempts (default: 3)
  "priority": 0,                   // Optional: Priority (higher = first, default: 0)
  "run_at": "2025-11-04T10:30:00Z", // Optional: Schedule for future execution
  "timeout": 300                   // Optional: Timeout in seconds (default: 300)
}
```

### Job States

| State | Description |
|-------|-------------|
| `pending` | Waiting to be picked up by a worker |
| `processing` | Currently being executed |
| `completed` | Successfully executed |
| `failed` | Failed, but retryable |
| `dead` | Permanently failed (moved to DLQ) |

## 🔄 Job Lifecycle

1. **Enqueue**: Job is created with state `pending`
2. **Pickup**: Worker picks up job, state changes to `processing`
3. **Execution**: Command is executed
4. **Success**: State changes to `completed`
5. **Failure**: State changes to `failed`, retry scheduled with exponential backoff
6. **Retry**: After backoff delay, job returns to `pending` for retry
7. **DLQ**: After max retries, job moves to `dead` state (DLQ)

## ⚙️ Configuration

### Available Configuration Keys

- `max-retries`: Maximum retry attempts (default: 3)
- `backoff-base`: Base for exponential backoff calculation (default: 2)
- `default-timeout`: Default job timeout in seconds (default: 300)
- `worker-poll-interval`: Worker polling interval in seconds (default: 1)
- `web-dashboard-port`: Web dashboard port (default: 8080)

### Example Configuration

```bash
# Set max retries to 5
queuectl config set max-retries 5

# Set backoff base to 3
queuectl config set backoff-base 3

# View all configuration
queuectl config show
```

## 📊 Usage Examples

### Example 1: Basic Job Execution

```bash
# Enqueue a simple job
queuectl enqueue "{""id"":""hello"",""command"":""echo Hello World""}"

# Start a worker
queuectl worker start --count 1

# Check status
queuectl status

# View completed jobs
queuectl list --state completed
```

### Example 2: Job with Retries

```bash
# Enqueue a job that might fail
queuectl enqueue "{""id"":""retry-test"",""command"":""exit 1"",""max_retries"":3}"

# Start workers
queuectl worker start --count 2

# Monitor retries
queuectl list --state failed

# Check DLQ after retries exhausted
queuectl dlq list
```

### Example 3: Priority Jobs

```bash
# Enqueue high priority job
queuectl enqueue "{""id"":""urgent"",""command"":""echo urgent"",""priority"":10}"

# Enqueue normal priority job
queuectl enqueue "{""id"":""normal"",""command"":""echo normal"",""priority"":0}"

# High priority job will be processed first
queuectl worker start --count 1
```

### Example 4: Scheduled Jobs

```cmd
:: Schedule job for future execution
queuectl enqueue "{""id"":""scheduled"",""command"":""echo scheduled"",""run_at"":""2025-11-04T15:30:00Z""}"

:: Job will be picked up only after the scheduled time
queuectl worker start --count 1
```

### Example 5: Job with Timeout

```cmd
:: Enqueue job with timeout
queuectl enqueue "{""id"":""timeout-test"",""command"":""timeout /t 10 >nul"",""timeout"":5}"

:: Job will timeout after 5 seconds
queuectl worker start --count 1
```

## 🏗️ Architecture

### System Components

```
┌─────────────┐
│   CLI       │  User Interface
└──────┬──────┘
       │
┌──────▼─────────────────────────────────────┐
│         Storage Layer (SQLite)             │
│  - Job persistence                         │
│  - Atomic locking                          │
│  - State management                        │
└──────┬─────────────────────────────────────┘
       │
┌──────▼─────────────────────────────────────┐
│         Scheduler                           │
│  - Job execution                           │
│  - Retry logic                             │
│  - Exponential backoff                     │
│  - DLQ management                          │
└──────┬─────────────────────────────────────┘
       │
┌──────▼─────────────────────────────────────┐
│         Worker Manager                      │
│  - Worker lifecycle                        │
│  - Graceful shutdown                       │
│  - Parallel processing                     │
└──────┬─────────────────────────────────────┘
       │
┌──────▼─────────────────────────────────────┐
│         Workers (Threads)                   │
│  - Job processing                          │
│  - Database-level locking                  │
└────────────────────────────────────────────┘
```

### Key Design Decisions

1. **SQLite Storage**: Lightweight, file-based, no external dependencies
2. **Database-Level Locking**: Atomic updates prevent race conditions
3. **Thread-Based Workers**: Efficient for I/O-bound job execution
4. **Exponential Backoff**: `delay = base ^ attempts` seconds
5. **Priority Queue**: SQL ORDER BY priority DESC, created_at ASC

### Data Flow

1. **Enqueue**: Job → Storage (SQLite) → State: `pending`
2. **Worker Loop**: Poll storage → Get next job → Atomic lock → Process
3. **Execution**: Execute command → Capture output → Update state
4. **Retry Logic**: On failure → Calculate backoff → Schedule retry
5. **DLQ**: Max retries exceeded → Move to `dead` state

## 🧪 Testing

### Run Test Scenarios

```cmd
python test_scenarios.py
```

This will run the following test scenarios:

1. **Basic Job Completion**: Verify successful job execution
2. **Failed Job Retry and DLQ**: Test retry mechanism and DLQ
3. **Multiple Workers**: Verify parallel processing without overlap
4. **Invalid Command**: Test graceful error handling
5. **Persistence**: Verify data survives restarts

### Manual Testing

```bash
# Test 1: Basic functionality
queuectl enqueue "{""id"":""test1"",""command"":""echo test""}"
queuectl worker start --count 1
# Wait a few seconds
queuectl list --state completed

# Test 2: Retry mechanism
queuectl enqueue "{""id"":""test2"",""command"":""exit 1"",""max_retries"":2}"
queuectl worker start --count 1
# Wait for retries
queuectl list --state failed
queuectl dlq list

# Test 3: Multiple workers
for /L %i in (1,1,10) do queuectl enqueue "{""id"":""job%i"",""command"":""echo job%i""}"
queuectl worker start --count 3
# Wait
queuectl status
```

## 📁 Project Structure

```
FLAM_proje/
├── queuectl/              # Main package
│   ├── __init__.py
│   ├── models.py          # Job model and states
│   ├── storage.py          # SQLite persistence layer
│   ├── scheduler.py       # Job execution and retry logic
│   ├── worker.py           # Worker management
│   ├── config.py           # Configuration management
│   ├── cli.py              # CLI interface
│   ├── metrics.py          # Metrics collection
│   ├── logger.py           # Logging utilities
│   └── web_dashboard.py    # Web dashboard
├── test_scenarios.py       # Test validation scripts
├── requirements.txt        # Python dependencies
├── setup.py                # Package setup
├── README.md               # This file
└── .gitignore             # Git ignore rules
```

## 🔧 Assumptions & Trade-offs

### Assumptions

1. **Single Machine**: Designed for single-machine deployment (not distributed)
2. **Shell Commands**: Jobs execute as shell commands (system-dependent)
3. **SQLite**: File-based database suitable for moderate workloads
4. **Threading**: Thread-based workers (suitable for I/O-bound tasks)

### Trade-offs

1. **SQLite vs PostgreSQL**: Chose SQLite for simplicity and zero-configuration
2. **File Locking vs DB Locking**: Used database-level atomic updates for reliability
3. **Threads vs Processes**: Used threads for efficiency (can be changed to processes)
4. **Synchronous Execution**: Jobs execute synchronously (could be async for better throughput)

### Limitations

1. **No Distributed Support**: Single-machine only (no multi-node)
2. **No Job Dependencies**: Jobs cannot depend on other jobs
3. **No Job Cancellation**: Cannot cancel running jobs (only graceful shutdown)
4. **Limited Scalability**: SQLite may become bottleneck at very high throughput

## 🚨 Troubleshooting

### Workers Not Processing Jobs

```bash
# Check worker status
queuectl status

# Verify workers are running
queuectl worker start --count 1

# Check for errors in logs
ls logs/
```

### Jobs Stuck in Processing

If jobs are stuck in `processing` state (e.g., after crash):

```bash
# Manually reset job state (requires direct DB access or add reset command)
# Or restart workers - they will handle cleanup
```

### Database Locked

If you see "database is locked" errors:

```bash
# Stop all workers
queuectl worker stop

# Wait a moment
sleep 2

# Restart
queuectl worker start --count 1
```

## 📈 Performance Considerations

- **Worker Count**: Start with 2-4 workers, adjust based on workload
- **Poll Interval**: Lower interval = faster pickup but more DB queries
- **Backoff Base**: Higher base = longer delays between retries
- **Database**: SQLite performs well for < 1000 concurrent jobs

## 🔐 Security Considerations

- **Command Execution**: Jobs execute with same privileges as QueueCTL process
- **Input Validation**: Validate job JSON before execution
- **File Permissions**: Ensure database file has appropriate permissions
- **Network**: Web dashboard binds to 0.0.0.0 (all interfaces) - restrict in production

## 📝 License

This project is created as part of a backend developer internship assignment.

## 🤝 Contributing

This is an assignment project. For questions or issues, please refer to the assignment guidelines.

## 📞 Support

For issues or questions:
1. Check the README
2. Review test scenarios
3. Check logs in `logs/` directory
4. Verify configuration with `queuectl config show`

---

## ✅ Checklist

- [x] Working CLI application (`queuectl`)
- [x] Persistent job storage (SQLite)
- [x] Multiple worker support
- [x] Retry mechanism with exponential backoff
- [x] Dead Letter Queue
- [x] Configuration management
- [x] Clean CLI interface
- [x] Comprehensive README
- [x] Code structure with separation of concerns
- [x] Test scenarios for validation
- [x] Bonus features (timeout, priority, scheduled jobs, logging, metrics, web dashboard)

---

**Built with ❤️ for the Backend Developer Internship Assignment**

