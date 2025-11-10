# QueueCTL Quick Start Guide

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install QueueCTL
pip install -e .
```

## Basic Usage

### 1. Enqueue Your First Job

```bash
queuectl enqueue '{"id":"my-job","command":"echo Hello World"}'
```

### 2. Start a Worker

```bash
queuectl worker start --count 1
```

### 3. Check Status

```bash
queuectl status
```

### 4. View Jobs

```bash
# List all jobs
queuectl list

# List only completed jobs
queuectl list --state completed
```

### 5. Stop Workers

```bash
queuectl worker stop
```

## Common Workflows

### Workflow 1: Process Multiple Jobs

```bash
# Enqueue multiple jobs
for i in {1..10}; do
  queuectl enqueue "{\"id\":\"job$i\",\"command\":\"echo Job $i\"}"
done

# Start 3 workers
queuectl worker start --count 3

# Monitor progress
queuectl status

# Stop when done
queuectl worker stop
```

### Workflow 2: Handle Failures with Retries

```bash
# Enqueue a job that might fail
queuectl enqueue '{"id":"retry-job","command":"some-command","max_retries":3}'

# Start workers
queuectl worker start --count 2

# Check failed jobs
queuectl list --state failed

# After retries exhausted, check DLQ
queuectl dlq list

# Retry a DLQ job
queuectl dlq retry retry-job
```

### Workflow 3: Priority Jobs

```bash
# Low priority job
queuectl enqueue '{"id":"low","command":"echo low","priority":1}'

# High priority job
queuectl enqueue '{"id":"high","command":"echo high","priority":10}'

# High priority will be processed first
queuectl worker start --count 1
```

### Workflow 4: Scheduled Jobs

```bash
# Schedule job for future (ISO format)
queuectl enqueue '{
  "id":"scheduled",
  "command":"echo scheduled",
  "run_at":"2025-11-04T15:30:00Z"
}'

# Job will only run after the scheduled time
queuectl worker start --count 1
```

### Workflow 5: Web Dashboard

```bash
# Start dashboard
queuectl dashboard

# Open browser to http://localhost:8080
# Dashboard auto-refreshes every 5 seconds
```

## Configuration

```bash
# View current config
queuectl config show

# Set max retries
queuectl config set max-retries 5

# Set backoff base (for exponential backoff)
queuectl config set backoff-base 3

# Set default timeout (seconds)
queuectl config set default-timeout 600
```

## Testing

Run the test scenarios:

```bash
python test_scenarios.py
```

Or run the demo script:

```bash
# Linux/Mac
bash demo.sh

# Windows
demo.bat
```

## Troubleshooting

### Workers not processing jobs?

```bash
# Check if workers are running
queuectl status

# Restart workers
queuectl worker stop
queuectl worker start --count 2
```

### Jobs stuck in processing?

```bash
# Stop and restart workers
queuectl worker stop
sleep 2
queuectl worker start --count 1
```

### Database locked errors?

```bash
# Stop all workers first
queuectl worker stop

# Wait a moment
sleep 2

# Restart
queuectl worker start --count 1
```

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check [test_scenarios.py](test_scenarios.py) for validation examples
- Explore the web dashboard for real-time monitoring

