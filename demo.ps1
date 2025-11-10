# QueueCTL Demo Script for PowerShell
# This script demonstrates the core functionality of QueueCTL

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "QueueCTL Demo" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Clean up any existing data
Write-Host "Cleaning up..." -ForegroundColor Yellow
Remove-Item queuectl.db -ErrorAction SilentlyContinue
Remove-Item .queuectl_*.lock -ErrorAction SilentlyContinue
Remove-Item .queuectl_workers.pid -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "=== Step 1: Enqueue Jobs ===" -ForegroundColor Green
Write-Host ""

# Enqueue a simple successful job
Write-Host "Enqueuing job 'demo1' (successful)..." -ForegroundColor White
$json1 = '{"id":"demo1","command":"echo Hello from QueueCTL","max_retries":3}'
queuectl enqueue $json1

# Enqueue a job that will fail
Write-Host "Enqueuing job 'demo2' (will fail and retry)..." -ForegroundColor White
$json2 = '{"id":"demo2","command":"exit 1","max_retries":2}'
queuectl enqueue $json2

# Enqueue multiple jobs
Write-Host "Enqueuing multiple jobs..." -ForegroundColor White
$json3 = '{"id":"demo3","command":"echo Job 3","priority":3}'
$json4 = '{"id":"demo4","command":"echo Job 4","priority":4}'
$json5 = '{"id":"demo5","command":"echo Job 5","priority":5}'
queuectl enqueue $json3
queuectl enqueue $json4
queuectl enqueue $json5

Write-Host ""
Write-Host "=== Step 2: Check Status ===" -ForegroundColor Green
queuectl status

Write-Host ""
Write-Host "=== Step 3: Start Workers ===" -ForegroundColor Green
Write-Host "Starting 2 workers..." -ForegroundColor White
Start-Process -NoNewWindow -FilePath "queuectl" -ArgumentList "worker","start","--count","2"

Write-Host "Workers started"
Write-Host "Waiting for jobs to process..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host ""
Write-Host "=== Step 4: Check Job Status ===" -ForegroundColor Green
Write-Host ""
Write-Host "Completed jobs:" -ForegroundColor White
queuectl list --state completed

Write-Host ""
Write-Host "Failed jobs:" -ForegroundColor White
queuectl list --state failed

Write-Host ""
Write-Host "=== Step 5: Wait for Retries ===" -ForegroundColor Green
Write-Host "Waiting for retry mechanism..." -ForegroundColor Yellow
Start-Sleep -Seconds 8

Write-Host ""
Write-Host "=== Step 6: Check DLQ ===" -ForegroundColor Green
queuectl dlq list

Write-Host ""
Write-Host "=== Step 7: Final Status ===" -ForegroundColor Green
queuectl status

Write-Host ""
Write-Host "=== Step 8: Stop Workers ===" -ForegroundColor Green
queuectl worker stop

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Demo Complete!" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Try these commands:" -ForegroundColor Yellow
Write-Host "  queuectl status          - View system status"
Write-Host "  queuectl list            - List all jobs"
Write-Host "  queuectl dlq list        - View Dead Letter Queue"
Write-Host "  queuectl config show     - Show configuration"
Write-Host "  queuectl dashboard       - Start web dashboard"


