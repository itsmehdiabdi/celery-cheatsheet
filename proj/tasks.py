"""
Celery tasks: building blocks of the application.

Concepts covered (see docstrings below):
- Defining tasks with @app.task
- Task names (automatic vs explicit)
- bind=True and self.request (task id, args, retries, etc.)
- Retries: retry(), autoretry_for, countdown, max_retries
- Task states: PENDING, STARTED, SUCCESS, FAILURE, RETRY, REVOKED; update_state()
- Options: ignore_result, rate_limit, time_limit, acks_late, track_started

Reference: https://docs.celeryq.dev/en/stable/userguide/tasks.html
"""
from celery.utils.log import get_task_logger

from proj.celery import app

logger = get_task_logger(__name__)


# -----------------------------------------------------------------------------
# Basics: simple tasks
# -----------------------------------------------------------------------------

@app.task
def add(x: int, y: int) -> int:
    """
    Add two numbers. Used in first-steps examples and canvas (chain, group, chord).

    Task name is auto-generated as 'proj.tasks.add' (module + function).
    """
    logger.info(f"Adding {x} and {y}")
    import time
    time.sleep(1)
    return x + y


@app.task
def mul(x: int, y: int) -> int:
    """Multiply two numbers. Used in chains and examples."""
    return x * y


@app.task
def xsum(numbers: list) -> float:
    """
    Sum a list of numbers. Used as chord callback: group of tasks -> single result.

    Chord requires a result backend; tasks in the header must not use ignore_result=True.
    """
    return sum(numbers)


# -----------------------------------------------------------------------------
# Task with explicit name (useful for routing or stable naming across modules)
# -----------------------------------------------------------------------------

@app.task(name="proj.tasks.heavy_task")
def heavy_task(n: int) -> int:
    """
    Example task routed to 'heavy' queue (see proj.config task_routes).
    Workers that consume from 'heavy' will run this: celery -A proj worker -Q heavy,celery
    """
    return n * 2


# -----------------------------------------------------------------------------
# Bound task: bind=True gives access to self (task instance) and self.request
# -----------------------------------------------------------------------------

@app.task(bind=True)
def show_request_info(self, tag: str) -> dict:
    """
    Demonstrates Task.request: id, args, kwargs, retries, hostname, etc.
    Use bind=True when you need retry(), update_state(), or request metadata.
    """
    return {
        "task_id": self.request.id,
        "args": self.request.args,
        "kwargs": self.request.kwargs,
        "retries": self.request.retries,
        "hostname": self.request.hostname,
        "tag": tag,
    }


# -----------------------------------------------------------------------------
# Retries: manual retry and autoretry_for
# -----------------------------------------------------------------------------

@app.task(bind=True, max_retries=3)
def flaky_task(self, fail_times: int = 0) -> str:
    """
    Fails the first `fail_times` attempts then succeeds.
    Uses self.retry(exc=..., countdown=...) to re-queue the task.
    retry() raises Retry exception; code after retry() is not run.
    """
    if self.request.retries < fail_times:
        raise self.retry(exc=Exception("simulated failure"), countdown=1)
    return "ok"


@app.task(autoretry_for=(ConnectionError,), retry_backoff=True, retry_backoff_max=60)
def fetch_url(url: str) -> str:
    """
    Autoretry: on ConnectionError the task is retried automatically with
    exponential backoff (1s, 2s, 4s, ... up to retry_backoff_max).
    retry_jitter (default True) adds randomness to avoid thundering herd.
    """
    import urllib.request
    with urllib.request.urlopen(url, timeout=5) as r:
        return r.read().decode("utf-8", errors="replace")[:200]


# -----------------------------------------------------------------------------
# Custom state and progress (update_state)
# -----------------------------------------------------------------------------

@app.task(bind=True)
def progress_task(self, steps: int) -> str:
    """
    Reports custom state 'PROGRESS' with meta (current, total).
    Clients can subscribe to state updates or poll result.info for progress.
    """
    for i in range(steps):
        if not self.request.called_directly:
            self.update_state(
                state="PROGRESS",
                meta={"current": i, "total": steps, "pct": 100 * i // steps},
            )
        # Simulate work
        import time
        time.sleep(0.2)
    return "done"


# -----------------------------------------------------------------------------
# Task options: ignore_result, track_started
# -----------------------------------------------------------------------------

@app.task(ignore_result=True)
def fire_and_forget(msg: str) -> None:
    """
    Result is not stored. Use for logging, notifications, or any task where
    the caller does not need the return value. Saves backend storage and I/O.
    """
    logger.info("fire_and_forget: %s", msg)
    return "done"


@app.task(bind=True, track_started=True)
def long_running(self, duration_sec: float) -> str:
    """
    With track_started=True the task state becomes STARTED when execution
    begins (otherwise only PENDING -> SUCCESS/FAILURE). Useful for long tasks
    so clients know the task is actually running.
    """
    import time
    time.sleep(duration_sec)
    return f"slept {duration_sec}s"


# -----------------------------------------------------------------------------
# Error handling: expected exceptions (throws)
# -----------------------------------------------------------------------------

@app.task(throws=(ValueError,))
def strict_add(x: int, y: int) -> int:
    """
    throws=(ValueError,) marks ValueError as "expected". Worker logs it at INFO
    without traceback; result backend still gets FAILURE. Use for validation
    errors you don't want to treat as system errors.
    """
    if not isinstance(x, int) or not isinstance(y, int):
        raise ValueError("ints only")
    return x + y


# -----------------------------------------------------------------------------
# Task that uses task lifecycle handlers (on_success, on_failure, after_return)
# -----------------------------------------------------------------------------

from celery import Task

class LoggingTask(Task):
    """Custom base: log on success/failure. Set on task with base=LoggingTask."""

    def on_success(self, retval, task_id, args, kwargs):
        logger.info("Task %s succeeded: %s", task_id, retval)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.warning("Task %s failed: %s", task_id, exc)

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        logger.debug("Task %s finished with status %s", task_id, status)


@app.task(base=LoggingTask)
def task_with_handlers(x: int, y: int) -> int:
    """Uses LoggingTask base for on_success/on_failure/after_return logging."""
    return x + y
