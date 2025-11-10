@echo off
REM QueueCTL Demo Script for Windows
REM This script demonstrates the core functionality of QueueCTL

echo ==========================================
echo QueueCTL Demo
echo ==========================================
echo.

REM Clean up any existing data
echo Cleaning up...
if exist queuectl.db del queuectl.db
if exist .queuectl_*.lock del .queuectl_*.lock
if exist .queuectl_workers.pid del .queuectl_workers.pid

echo.
echo === Step 1: Enqueue Jobs ===
echo.

REM Enqueue a simple successful job
echo Enqueuing job 'demo1' (successful)...
queuectl enqueue "{\"id\":\"demo1\",\"command\":\"echo Hello from QueueCTL\",\"max_retries\":3}"

REM Enqueue a job that will fail
echo Enqueuing job 'demo2' (will fail and retry)...
queuectl enqueue "{\"id\":\"demo2\",\"command\":\"exit 1\",\"max_retries\":2}"

REM Enqueue multiple jobs
echo Enqueuing multiple jobs...
queuectl enqueue "{\"id\":\"demo3\",\"command\":\"echo Job 3\",\"priority\":3}"
queuectl enqueue "{\"id\":\"demo4\",\"command\":\"echo Job 4\",\"priority\":4}"
queuectl enqueue "{\"id\":\"demo5\",\"command\":\"echo Job 5\",\"priority\":5}"

echo.
echo === Step 2: Check Status ===
queuectl status

echo.
echo === Step 3: Start Workers ===
echo Starting 2 workers...
start /B queuectl worker start --count 2

echo Workers started
echo Waiting for jobs to process...
timeout /t 5 /nobreak >nul

echo.
echo === Step 4: Check Job Status ===
echo.
echo Completed jobs:
queuectl list --state completed

echo.
echo Failed jobs:
queuectl list --state failed

echo.
echo === Step 5: Wait for Retries ===
echo Waiting for retry mechanism...
timeout /t 8 /nobreak >nul

echo.
echo === Step 6: Check DLQ ===
queuectl dlq list

echo.
echo === Step 7: Final Status ===
queuectl status

echo.
echo === Step 8: Stop Workers ===
queuectl worker stop

echo.
echo ==========================================
echo Demo Complete!
echo ==========================================
echo.
echo Try these commands:
echo   queuectl status          - View system status
echo   queuectl list            - List all jobs
echo   queuectl dlq list        - View Dead Letter Queue
echo   queuectl config show     - Show configuration
echo   queuectl dashboard       - Start web dashboard

pause

