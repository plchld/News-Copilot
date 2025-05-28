# Backend Setup Guide

## Initial Setup

### 1. Fix the Migration Issue

The error you encountered is because Django's admin app is trying to reference the User model before it's created. Here's how to fix it:

**Option A: Use the fix script (Recommended)**
```bash
cd backend
python fix_migrations.py
```

**Option B: Manual steps**
```bash
# 1. Create migrations for core app first (contains User model)
python manage.py makemigrations core

# 2. Create migrations for other apps
python manage.py makemigrations authentication news_aggregator api

# 3. Apply migrations in specific order
python manage.py migrate contenttypes
python manage.py migrate auth  
python manage.py migrate core  # Creates User table
python manage.py migrate admin  # Now admin can reference User
python manage.py migrate  # Apply all remaining migrations
```

### 2. Create Superuser
```bash
python manage.py createsuperuser
```

### 3. Run the Development Server
```bash
python manage.py runserver
```

## If You Need to Start Over

If you encounter issues and need to reset:

```bash
# Option 1: Reset database (CAUTION: Deletes all data)
python reset_db.py

# Option 2: Delete migration files manually
# Delete all migration files except __init__.py in each app's migrations folder
# Then run fix_migrations.py again
```

## Common Issues

### "No changes detected" when running makemigrations

Make sure:
1. The app is in INSTALLED_APPS
2. The app has a models.py file
3. The migrations folder exists with __init__.py

### "relation 'users' does not exist"

This means the User model hasn't been created yet. Run the fix_migrations.py script.

### Debug mode shows SQL queries

This is normal in development. To disable, set `DEBUG = False` in settings or remove django-debug-toolbar.

## Verify Setup

After successful migration:

1. Check admin interface: http://localhost:8000/admin/
2. Test API: http://localhost:8000/api/health/
3. View API docs: http://localhost:8000/api/docs/

## Next Steps

1. Start Celery worker (in new terminal):
   ```bash
   celery -A config worker -l info
   ```

2. Start Redis (if not using Docker):
   ```bash
   redis-server
   ```

3. Process a test article:
   ```bash
   python manage.py process_article https://www.kathimerini.gr/someurl
   ```