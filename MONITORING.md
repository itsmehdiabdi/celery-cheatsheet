# Celery Monitoring & Management

## Real-time Event Monitor
```bash
celery -A proj events
```
Monitor Celery events in real-time from the terminal.

## Flower Web UI
```bash
pip install flower
celery -A proj flower
```
Web-based real-time monitor and admin tool for Celery (runs on http://localhost:5555).

## Queue Management
```bash
celery -A proj purge
```
Purge all messages from all configured task queues.

## Task Inspection
```bash
celery -A proj inspect active
```
List currently executing tasks.

```bash
celery -A proj inspect scheduled
```
List tasks scheduled for future execution.

```bash
celery -A proj inspect registered
```
List all registered task names.
