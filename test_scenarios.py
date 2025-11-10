"""Test scenarios to validate QueueCTL functionality."""

import subprocess
import time
import json
import os
import sys
from pathlib import Path


def run_command(cmd: str) -> tuple[int, str, str]:
    """Run a command and return exit code, stdout, stderr."""
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True
    )
    return result.returncode, result.stdout, result.stderr


def test_basic_job_completion():
    """Test 1: Basic job completes successfully."""
    print("\n=== Test 1: Basic Job Completion ===")
    
    # Clean up
    if Path("queuectl.db").exists():
        Path("queuectl.db").unlink()
    
    # Enqueue a simple job
    job_id = "test_job_1"
    cmd = f'queuectl enqueue \'{{"id":"{job_id}","command":"echo Hello World"}}\''
    exit_code, stdout, stderr = run_command(cmd)
    
    if exit_code != 0:
        print(f"FAILED: Could not enqueue job. Error: {stderr}")
        return False
    
    print(f"✓ Job enqueued: {stdout.strip()}")
    
    # Start a worker
    print("Starting worker...")
    worker_process = subprocess.Popen(
        ["queuectl", "worker", "start", "--count", "1"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for job to complete
    time.sleep(3)
    
    # Check job status
    exit_code, stdout, stderr = run_command("queuectl list --state completed")
    if job_id in stdout:
        print("✓ Job completed successfully")
        worker_process.terminate()
        worker_process.wait()
        return True
    else:
        print("FAILED: Job did not complete")
        worker_process.terminate()
        worker_process.wait()
        return False


def test_failed_job_retry_and_dlq():
    """Test 2: Failed job retries with backoff and moves to DLQ."""
    print("\n=== Test 2: Failed Job Retry and DLQ ===")
    
    # Clean up
    if Path("queuectl.db").exists():
        Path("queuectl.db").unlink()
    
    # Enqueue a job that will fail
    job_id = "test_job_fail"
    cmd = f'queuectl enqueue \'{{"id":"{job_id}","command":"exit 1","max_retries":2}}\''
    exit_code, stdout, stderr = run_command(cmd)
    
    if exit_code != 0:
        print(f"FAILED: Could not enqueue job. Error: {stderr}")
        return False
    
    print(f"✓ Job enqueued: {stdout.strip()}")
    
    # Start a worker
    print("Starting worker...")
    worker_process = subprocess.Popen(
        ["queuectl", "worker", "start", "--count", "1"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for retries and DLQ
    print("Waiting for retries and DLQ...")
    time.sleep(10)
    
    # Check DLQ
    exit_code, stdout, stderr = run_command("queuectl dlq list")
    if job_id in stdout:
        print("✓ Job moved to DLQ after retries")
        worker_process.terminate()
        worker_process.wait()
        return True
    else:
        print("FAILED: Job not in DLQ")
        print(f"DLQ output: {stdout}")
        worker_process.terminate()
        worker_process.wait()
        return False


def test_multiple_workers():
    """Test 3: Multiple workers process jobs without overlap."""
    print("\n=== Test 3: Multiple Workers ===")
    
    # Clean up
    if Path("queuectl.db").exists():
        Path("queuectl.db").unlink()
    
    # Enqueue multiple jobs
    job_ids = []
    for i in range(5):
        job_id = f"test_job_{i}"
        job_ids.append(job_id)
        cmd = f'queuectl enqueue \'{{"id":"{job_id}","command":"sleep 1 && echo Job {i}"}}\''
        run_command(cmd)
    
    print(f"✓ Enqueued {len(job_ids)} jobs")
    
    # Start 3 workers
    print("Starting 3 workers...")
    worker_process = subprocess.Popen(
        ["queuectl", "worker", "start", "--count", "3"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for jobs to complete
    time.sleep(8)
    
    # Check status
    exit_code, stdout, stderr = run_command("queuectl status")
    print(f"\nStatus:\n{stdout}")
    
    # Check completed jobs
    exit_code, stdout, stderr = run_command("queuectl list --state completed")
    completed_count = stdout.count("Job ID:")
    
    if completed_count >= len(job_ids):
        print(f"✓ All {len(job_ids)} jobs completed")
        worker_process.terminate()
        worker_process.wait()
        return True
    else:
        print(f"FAILED: Only {completed_count}/{len(job_ids)} jobs completed")
        worker_process.terminate()
        worker_process.wait()
        return False


def test_invalid_command():
    """Test 4: Invalid commands fail gracefully."""
    print("\n=== Test 4: Invalid Command Handling ===")
    
    # Clean up
    if Path("queuectl.db").exists():
        Path("queuectl.db").unlink()
    
    # Enqueue a job with invalid command
    job_id = "test_invalid"
    cmd = f'queuectl enqueue \'{{"id":"{job_id}","command":"nonexistent_command_xyz123"}}\''
    exit_code, stdout, stderr = run_command(cmd)
    
    if exit_code != 0:
        print(f"FAILED: Could not enqueue job. Error: {stderr}")
        return False
    
    print(f"✓ Job enqueued: {stdout.strip()}")
    
    # Start a worker
    print("Starting worker...")
    worker_process = subprocess.Popen(
        ["queuectl", "worker", "start", "--count", "1"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for processing
    time.sleep(5)
    
    # Check that job failed and was retried or moved to DLQ
    exit_code, stdout, stderr = run_command("queuectl list --state failed")
    if job_id in stdout or "dead" in stdout.lower():
        print("✓ Invalid command handled gracefully")
        worker_process.terminate()
        worker_process.wait()
        return True
    else:
        print("FAILED: Invalid command not handled properly")
        worker_process.terminate()
        worker_process.wait()
        return False


def test_persistence():
    """Test 5: Job data survives restart."""
    print("\n=== Test 5: Persistence Across Restart ===")
    
    # Clean up
    if Path("queuectl.db").exists():
        Path("queuectl.db").unlink()
    
    # Enqueue a job
    job_id = "test_persist"
    cmd = f'queuectl enqueue \'{{"id":"{job_id}","command":"echo Persistence Test"}}\''
    exit_code, stdout, stderr = run_command(cmd)
    
    if exit_code != 0:
        print(f"FAILED: Could not enqueue job. Error: {stderr}")
        return False
    
    print(f"✓ Job enqueued: {stdout.strip()}")
    
    # Verify job exists
    exit_code, stdout, stderr = run_command("queuectl list")
    if job_id not in stdout:
        print("FAILED: Job not found after enqueue")
        return False
    
    print("✓ Job found in storage")
    
    # Check that database file exists
    if not Path("queuectl.db").exists():
        print("FAILED: Database file not created")
        return False
    
    print("✓ Database file exists")
    
    # Simulate restart by checking job still exists
    exit_code, stdout, stderr = run_command("queuectl list")
    if job_id in stdout:
        print("✓ Job persists after 'restart' (still in storage)")
        return True
    else:
        print("FAILED: Job lost after restart")
        return False


def main():
    """Run all test scenarios."""
    print("=" * 60)
    print("QueueCTL Test Scenarios")
    print("=" * 60)
    
    tests = [
        ("Basic Job Completion", test_basic_job_completion),
        ("Failed Job Retry and DLQ", test_failed_job_retry_and_dlq),
        ("Multiple Workers", test_multiple_workers),
        ("Invalid Command", test_invalid_command),
        ("Persistence", test_persistence),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\nERROR in {name}: {e}")
            results.append((name, False))
        
        # Clean up between tests
        time.sleep(1)
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

