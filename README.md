# Celery cheat sheet

A minimal, step-by-step learning repo for [Celery](https://docs.celeryq.dev/en/stable/) (distributed task queue).

Topics covered: 
    - Tasks (basics, names, bind, retry, states, options)
    - Calling (delay, apply_async, ETA, countdown, expires)
    - Canvas (signatures, chain, group, chord, map, starmap, chunks)
    - Periodic tasks


## Repo layout

- `proj/celery.py` – Celery app instance (broker, backend, config).
- `proj/config.py` – Centralized settings (beat schedule, routes, serialization).
- `proj/tasks.py` – All demo tasks and canvas usage; each task/section is documented in docstrings.
- `playground.py` – Examples for calling tasks and using chain/group/chord.
- `MONITORING.md` - Monitoring cheat sheet.

Learning path: read `proj/celery.py` → `proj/config.py` → `proj/tasks.py` → `playground.py` → `MONITORING.md`.
Use docstrings as the main reference.

## Requirements

- Python 3.8+
- A broker (Redis or RabbitMQ). Examples use Redis URLs by default.

## Setup

- make sure redis server is running.
    - Default broker: `redis://localhost:6379/0`. Override with env or in `proj/config.py`.
- Create a venv and install requirements.
- Run the worker:
    - In the repo root run `celery -A proj worker --loglevel=INFO`
- Create tasks and see the results. Two options:
    - In the repo root run `celery -A proj beat --loglevel=INFO` (Beat will enqueue periodic tasks defined in `proj.config`)
    - Or in the repo root run `python playground.py`

## Docs reference

Official docs: https://docs.celeryq.dev/en/stable/
