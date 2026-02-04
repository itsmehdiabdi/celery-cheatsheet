"""
Celery application instance (the "app").

This module is the entry point for everything in Celery: creating tasks,
starting workers, and configuration. Other modules must be able to import
this app (e.g. `from proj.celery import app`).

Concepts (from official docs):
- The first argument to Celery() is the app name; it's used for automatic
  task naming when tasks are defined in __main__.
- broker: URL of the message broker (required). Workers consume from here.
- backend: result backend URL (optional). If set, task states and return
  values are stored and you can use AsyncResult.get(), .ready(), .state.
- include: list of modules to import when the worker starts. Those modules
  must define tasks (with @app.task) so the worker can register them.
  Without include, the worker would not load proj.tasks by default.
"""
from celery import Celery

# Create the Celery application.
# - 'proj' is the app name (used in task naming).
# - broker: where to send/receive messages (Redis or amqp:// for RabbitMQ).
# - backend: where to store results; use None or omit to disable results.
app = Celery(
    "proj",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
    include=["proj.tasks"],
)

# Load configuration from proj.config (task_serializer, beat_schedule, etc.).
# Prefer central config over scattering settings in code.
app.config_from_object("proj.config")

if __name__ == "__main__":
    app.start()
