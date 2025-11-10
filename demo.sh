#!/bin/bash
# QueueCTL Demo Script
# This script demonstrates the core functionality of QueueCTL

echo "=========================================="
echo "QueueCTL Demo"
echo "=========================================="
echo ""

# Clean up any existing data
echo "Cleaning up..."
rm -f queuectl.db
rm -f .queuectl_*.lock
rm -f .queuectl_workers.pid

echo ""
echo "=== Step 1: Enqueue Jobs ==="
echo ""

# Enqueue a simple successful job
echo "Enqueuing job 'demo1' (successful)..."
queuectl enqueue '{"id":"demo1","command":"echo Hello from QueueCTL","max_retries":3}'

# Enqueue a job that will fail
echo "Enqueuing job 'demo2' (will fail and retry)..."
queuectl enqueue '{"id":"demo2","command":"exit 1","max_retries":2}'

# Enqueue multiple jobs
echo "Enqueuing multiple jobs..."
for i in {3..5}; do
    queuectl enqueue "{\"id\":\"demo$i\",\"command\":\"echo Job $i\",\"priority\":$i}"
done

echo ""
echo "=== Step 2: Check Status ==="
queuectl status

echo ""
echo "=== Step 3: Start Workers ==="
echo "Starting 2 workers in background..."
queuectl worker start --count 2 &
WORKER_PID=$!

echo "Workers started (PID: $WORKER_PID)"
echo "Waiting for jobs to process..."
sleep 5

echo ""
echo "=== Step 4: Check Job Status ==="
echo ""
echo "Completed jobs:"
queuectl list --state completed

echo ""
echo "Failed jobs:"
queuectl list --state failed

echo ""
echo "=== Step 5: Wait for Retries ==="
echo "Waiting for retry mechanism..."
sleep 8

echo ""
echo "=== Step 6: Check DLQ ==="
queuectl dlq list

echo ""
echo "=== Step 7: Final Status ==="
queuectl status

echo ""
echo "=== Step 8: Stop Workers ==="
queuectl worker stop

echo ""
echo "=========================================="
echo "Demo Complete!"
echo "=========================================="
echo ""
echo "Try these commands:"
echo "  queuectl status          - View system status"
echo "  queuectl list            - List all jobs"
echo "  queuectl dlq list        - View Dead Letter Queue"
echo "  queuectl config show     - Show configuration"
echo "  queuectl dashboard       - Start web dashboard"

