# Celery Setup Guide

## Installation

Celery is already included in the requirements.txt. To set it up:

1. **Install Redis** (if not using Docker):
   ```bash
   # Ubuntu/Debian
   sudo apt-get install redis-server
   
   # macOS
   brew install redis
   ```

2. **Start Redis**:
   ```bash
   # If using Docker
   docker run -d -p 6379:6379 redis:alpine
   
   # Or native
   redis-server
   ```

## Running Celery

### Development Setup

1. **Start Celery Worker** (in backend directory):
   ```bash
   celery -A config worker -l info
   ```

2. **Start Celery Beat** (for periodic tasks):
   ```bash
   celery -A config beat -l info
   ```

3. **Monitor with Flower** (optional):
   ```bash
   pip install flower
   celery -A config flower
   # Visit http://localhost:5555
   ```

### Production Setup

Use supervisord or systemd to manage Celery processes:

**systemd service example** (`/etc/systemd/system/celery.service`):
```ini
[Unit]
Description=Celery Service
After=network.target

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/path/to/backend
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/celery -A config worker --loglevel=info

[Install]
WantedBy=multi-user.target
```

## Celery Beat Schedule

Add periodic tasks in `config/celery.py`:

```python
from celery.schedules import crontab

app.conf.beat_schedule = {
    'cleanup-old-jobs': {
        'task': 'apps.news_aggregator.tasks.cleanup_old_jobs',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
}
```

## Testing Celery Tasks

1. **Test synchronously** (without Celery):
   ```python
   # In Django shell
   from apps.news_aggregator.tasks import process_article_task
   result = process_article_task.apply(args=['https://example.com/article']).get()
   ```

2. **Test asynchronously**:
   ```python
   # Queue the task
   from apps.news_aggregator.tasks import process_article_task
   task = process_article_task.delay('https://example.com/article')
   print(task.id)
   
   # Check status
   from celery.result import AsyncResult
   result = AsyncResult(task.id)
   print(result.status)
   print(result.result)
   ```

## Environment Variables

Add to `.env`:
```bash
# Redis/Celery
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## Monitoring & Debugging

1. **View Celery logs**:
   ```bash
   celery -A config worker -l debug
   ```

2. **Inspect active tasks**:
   ```bash
   celery -A config inspect active
   ```

3. **Purge all tasks**:
   ```bash
   celery -A config purge
   ```

## Common Issues

1. **Import errors**: Make sure DJANGO_SETTINGS_MODULE is set
2. **Task not found**: Ensure tasks are imported in `config/celery.py`
3. **Connection refused**: Check Redis is running on correct port