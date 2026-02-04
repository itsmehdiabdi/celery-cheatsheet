"""
Central Celery configuration.

Settings here apply app-wide. Reference: Configuration and defaults
https://docs.celeryq.dev/en/stable/userguide/configuration.html
"""
from celery.schedules import crontab

# -----------------------------------------------------------------------------
# Broker & result backend (can override proj/celery.py if needed)
# -----------------------------------------------------------------------------
# broker_url = "redis://localhost:6379/0"
# result_backend = "redis://localhost:6379/1"

# -----------------------------------------------------------------------------
# Serialization (security: prefer json over pickle for untrusted input)
# -----------------------------------------------------------------------------
task_serializer = "json"
result_serializer = "json"
accept_content = ["json"]

# -----------------------------------------------------------------------------
# Timezone (used for ETA, countdown, beat schedule)
# -----------------------------------------------------------------------------
timezone = "UTC"
enable_utc = True

# -----------------------------------------------------------------------------
# Result backend behaviour
# -----------------------------------------------------------------------------
# How long results are kept (seconds). Avoid unbounded growth.
result_expires = 3600
# Include extra metadata (e.g. task name, args repr) in result backend.
# result_extended = True

# -----------------------------------------------------------------------------
# Task defaults
# -----------------------------------------------------------------------------
# Don't store result by default for tasks that don't need it (saves backend I/O).
# Override per task with @app.task(ignore_result=False).
# task_ignore_result = False

# -----------------------------------------------------------------------------
# Periodic tasks (Celery Beat)
# -----------------------------------------------------------------------------
# Beat is a scheduler: it sends task messages at intervals. Only one beat
# process should run per schedule to avoid duplicate tasks.
# Schedule types: float (seconds), timedelta, crontab, solar.
beat_schedule = {
    "add-every-30-seconds": {
        "task": "proj.tasks.add",
        "schedule": 30.0,
        "args": (16, 16),
    },
    "mul-every-minute": {
        "task": "proj.tasks.mul",
        "schedule": 60.0,
        "args": (3, 7),
    },
    "crontab-example": {
        "task": "proj.tasks.add",
        "schedule": crontab(minute=0, hour="*/2"),  # every 2 hours
        "args": (1, 1),
    },
}

# -----------------------------------------------------------------------------
# Task routing (optional)
# -----------------------------------------------------------------------------
# Route tasks to named queues. Workers consume from queues with: -Q queue1,queue2
# Use for priority, separation of concerns, or dedicated worker pools.
task_routes = {
    "proj.tasks.heavy_task": {"queue": "heavy"},
    # "proj.tasks.add": {"queue": "hipri"},
}

# Optional: default queue for tasks not in task_routes
# task_default_queue = "celery"

# -----------------------------------------------------------------------------
# Task annotations (e.g. rate limits per task type)
# -----------------------------------------------------------------------------
# task_annotations = {"proj.tasks.add": {"rate_limit": "10/m"}}
