# Troubleshooting Guide

## Common Issues and Solutions

### 1. "You cannot call this from an async context"

**Issue**: Django ORM calls from async functions
**Solution**: Fixed in the updated management command using `sync_to_async`

### 2. "relation 'users' does not exist"

**Issue**: Migration dependency problem
**Solution**: Run the fix script:
```bash
python fix_migrations.py
```

### 3. XAI_API_KEY not found

**Issue**: Grok API key not set
**Solution**: Add to your `.env` file:
```bash
XAI_API_KEY=your_actual_api_key_here
```

### 4. Import errors for agents

**Issue**: Circular imports or missing modules
**Solution**: Test setup first:
```bash
python test_setup.py
```

### 5. Article extraction fails

**Issue**: Network issues or site blocking
**Solution**: Test with a simple extraction:
```bash
python manage.py test_extraction https://www.kathimerini.gr/some-article
```

## Testing Steps

### 1. Test Basic Setup
```bash
python test_setup.py
```

### 2. Test Article Extraction Only
```bash
python manage.py test_extraction https://www.amna.gr/some-article
```

### 3. Test Full Processing (requires XAI_API_KEY)
```bash
python manage.py process_article https://www.amna.gr/some-article --analyze
```

## Debug Mode

To see detailed SQL queries and debug info, the Django debug toolbar is enabled in development. You'll see SQL queries in the console.

To disable: Remove `django-debug-toolbar` from INSTALLED_APPS in development.py

## Environment Variables

Make sure these are set in your `.env` file:

```bash
# Required
POSTGRES_USER=newscopilot_user
POSTGRES_PASSWORD=newscopilot_pass123
POSTGRES_DB=newscopilot_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5499

# For AI features
XAI_API_KEY=your_xai_api_key_here

# Optional
DEBUG=True
DJANGO_LOG_LEVEL=DEBUG
```

## Testing Without AI

If you don't have an XAI API key yet, you can still test:

1. Article extraction: `python manage.py test_extraction <url>`
2. Database operations: `python test_setup.py`
3. Web interface: `python manage.py runserver`

## Next Steps

Once everything is working:

1. Test with a real article: 
   ```bash
   python manage.py test_extraction https://www.kathimerini.gr/politics/562049808/nea-voyli-apo-to-2027-se-kalyteri-topothesia/
   ```

2. If extraction works, try with AI analysis (needs XAI_API_KEY):
   ```bash
   python manage.py process_article <same_url> --analyze
   ```

3. Start the development server:
   ```bash
   python manage.py runserver
   ```