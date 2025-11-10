"""CLI interface for QueueCTL."""

import click
import json
import sys
import uuid
from datetime import datetime, timedelta
from dateutil.parser import parse
from queuectl.storage import Storage
from queuectl.scheduler import Scheduler
from queuectl.worker import WorkerManager
from queuectl.config import Config
from queuectl.models import Job, JobState
from queuectl.metrics import Metrics


# Global instances (initialized in main)
storage = None
scheduler = None
worker_manager = None
config = None
metrics = None


def init_components():
    """Initialize global components."""
    global storage, scheduler, worker_manager, config, metrics
    config = Config()
    storage = Storage(db_path=config.get("db_path"))
    scheduler = Scheduler(storage, config)
    worker_manager = WorkerManager(storage, scheduler, config)
    metrics = Metrics(storage)


@click.group()
@click.version_option(version="1.0.0")
def main():
    """QueueCTL - CLI-based background job queue system."""
    init_components()


@main.command()
@click.argument('job_data', type=str)
def enqueue(job_data):
    """Enqueue a new job.
    
    JOB_DATA: JSON string with job details (id, command, max_retries, priority, run_at, timeout)
    
    Example: queuectl enqueue '{"id":"job1","command":"echo hello","max_retries":3}'
    """
    try:
        data = json.loads(job_data)
        
        # Validate required fields
        if "id" not in data or "command" not in data:
            click.echo("Error: 'id' and 'command' are required fields", err=True)
            sys.exit(1)
        
        # Create job with defaults
        job = Job(
            id=data["id"],
            command=data["command"],
            max_retries=data.get("max_retries", config.get("max_retries")),
            priority=data.get("priority", 0),
            run_at=data.get("run_at"),
            timeout=data.get("timeout", config.get("default_timeout")),
        )
        
        # Add job to storage
        if storage.add_job(job):
            click.echo(f"Job '{job.id}' enqueued successfully")
            click.echo(f"  Command: {job.command}")
            click.echo(f"  State: {job.state}")
            click.echo(f"  Max Retries: {job.max_retries}")
        else:
            click.echo(f"Error: Job '{job.id}' already exists", err=True)
            sys.exit(1)
            
    except json.JSONDecodeError:
        click.echo("Error: Invalid JSON format", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.group()
def worker():
    """Manage worker processes."""
    pass


@worker.command()
@click.option('--count', default=1, type=int, help='Number of workers to start')
def start(count):
    """Start worker processes."""
    if count < 1:
        click.echo("Error: Worker count must be at least 1", err=True)
        sys.exit(1)
    
    worker_manager.start_workers(count)
    click.echo(f"Started {count} worker(s). Use 'queuectl worker stop' to stop them.")


@worker.command()
def stop():
    """Stop all running workers gracefully."""
    worker_manager.stop_all()
    click.echo("All workers stopped")


@main.command()
def status():
    """Show summary of job states and active workers."""
    stats = storage.get_stats()
    active_workers = worker_manager.get_worker_count()
    worker_status = worker_manager.get_worker_status()
    
    click.echo("=== QueueCTL Status ===")
    click.echo(f"\nActive Workers: {active_workers}")
    
    if worker_status:
        click.echo("\nWorker Details:")
        for w in worker_status:
            status_str = "running" if w["running"] else "stopped"
            current = f" (job: {w['current_job']})" if w["current_job"] else ""
            click.echo(f"  Worker {w['id']}: {status_str}{current}")
    
    click.echo("\nJob Statistics:")
    for state in JobState:
        count = stats.get(state.value, 0)
        click.echo(f"  {state.value.capitalize()}: {count}")
    
    click.echo(f"\nTotal Jobs: {stats.get('total', 0)}")
    
    # Show execution metrics
    exec_stats = metrics.get_execution_stats()
    if exec_stats["total_executions"] > 0:
        click.echo("\nExecution Metrics:")
        click.echo(f"  Total Executions: {exec_stats['total_executions']}")
        click.echo(f"  Avg Execution Time: {exec_stats['avg_execution_time']:.2f}s")
        click.echo(f"  Min Execution Time: {exec_stats['min_execution_time']:.2f}s")
        click.echo(f"  Max Execution Time: {exec_stats['max_execution_time']:.2f}s")


@main.command()
@click.option('--state', type=click.Choice(['pending', 'processing', 'completed', 'failed', 'dead']), help='Filter by job state')
@click.option('--limit', default=20, type=int, help='Maximum number of jobs to show')
def list(state, limit):
    """List jobs, optionally filtered by state."""
    jobs = storage.list_jobs(state=state, limit=limit)
    
    if not jobs:
        click.echo("No jobs found")
        return
    
    click.echo(f"=== Jobs ({len(jobs)} shown) ===")
    for job in jobs:
        click.echo(f"\nJob ID: {job.id}")
        click.echo(f"  Command: {job.command}")
        click.echo(f"  State: {job.state}")
        click.echo(f"  Attempts: {job.attempts}/{job.max_retries}")
        click.echo(f"  Priority: {job.priority}")
        click.echo(f"  Created: {job.created_at}")
        if job.error:
            click.echo(f"  Error: {job.error}")
        if job.next_retry_at:
            click.echo(f"  Next Retry: {job.next_retry_at}")


@main.group()
def dlq():
    """Manage Dead Letter Queue."""
    pass


@dlq.command()
def list():
    """List all jobs in Dead Letter Queue."""
    jobs = storage.get_dlq_jobs()
    
    if not jobs:
        click.echo("Dead Letter Queue is empty")
        return
    
    click.echo(f"=== Dead Letter Queue ({len(jobs)} jobs) ===")
    for job in jobs:
        click.echo(f"\nJob ID: {job.id}")
        click.echo(f"  Command: {job.command}")
        click.echo(f"  Attempts: {job.attempts}/{job.max_retries}")
        click.echo(f"  Error: {job.error}")
        click.echo(f"  Failed At: {job.updated_at}")


@dlq.command()
@click.argument('job_id', type=str)
def retry(job_id):
    """Reset a DLQ job back to pending state for retry."""
    job = storage.reset_job_from_dlq(job_id)
    
    if job:
        click.echo(f"Job '{job_id}' reset to pending state")
        click.echo(f"  Command: {job.command}")
        click.echo(f"  Attempts reset to 0")
    else:
        click.echo(f"Error: Job '{job_id}' not found in DLQ or cannot be reset", err=True)
        sys.exit(1)


@main.group()
def config():
    """Manage configuration."""
    pass


@config.command()
@click.argument('key', type=str)
@click.argument('value', type=str)
def set(key, value):
    """Set a configuration value.
    
    Available keys: max-retries, backoff-base, default-timeout, worker-poll-interval
    """
    # Convert value to appropriate type
    if key in ["max-retries", "default-timeout", "worker-poll-interval", "web-dashboard-port"]:
        try:
            value = int(value)
        except ValueError:
            click.echo(f"Error: '{key}' must be an integer", err=True)
            sys.exit(1)
    elif key == "backoff-base":
        try:
            value = float(value)
        except ValueError:
            click.echo(f"Error: '{key}' must be a number", err=True)
            sys.exit(1)
    
    # Map CLI key to config key
    key_map = {
        "max-retries": "max_retries",
        "backoff-base": "backoff_base",
        "default-timeout": "default_timeout",
        "worker-poll-interval": "worker_poll_interval",
        "web-dashboard-port": "web_dashboard_port",
    }
    
    config_key = key_map.get(key, key.replace("-", "_"))
    config.set(config_key, value)
    click.echo(f"Configuration '{key}' set to '{value}'")


@config.command()
def show():
    """Show current configuration."""
    all_config = config.get_all()
    click.echo("=== Configuration ===")
    for key, value in sorted(all_config.items()):
        click.echo(f"  {key}: {value}")


@main.command()
@click.option('--port', default=None, type=int, help='Port for web dashboard')
def dashboard(port):
    """Start web dashboard for monitoring."""
    from queuectl.web_dashboard import start_dashboard
    
    port = port or config.get("web_dashboard_port", 8080)
    click.echo(f"Starting web dashboard on http://localhost:{port}")
    click.echo("Press Ctrl+C to stop")
    
    start_dashboard(storage, worker_manager, metrics, port)


if __name__ == '__main__':
    main()

