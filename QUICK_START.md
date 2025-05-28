# Quick Start Guide

## Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL (recommended) or SQLite for development
- Chrome/Chromium browser (for enhanced extraction)

## Full Installation (Recommended)

### 1. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install all dependencies
pip install -r requirements.txt

# Create .env file with your configuration
cp .env.example .env
# Edit .env and add:
# - XAI_API_KEY (required for AI analysis)
# - Database settings (optional, defaults to SQLite)
# - Supabase settings (optional for authentication)

# Run database migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser for Django admin
python manage.py createsuperuser

# Start Django development server
python manage.py runserver 8000
```

### 2. Frontend Setup
```bash
# In a new terminal, navigate to frontend
cd frontend

# Install dependencies
npm install  # or pnpm install

# Create environment file
cp .env.example .env.local
# Edit .env.local and set:
# NEXT_PUBLIC_API_URL=http://localhost:8000/api

# Start Next.js development server
npm run dev  # or pnpm run dev
```

## Real-World Examples

### Basic Article Processing
```bash
cd backend

# Extract article content only
python manage.py process_article "https://www.kathimerini.gr/economy/562917774/i-agora-ergasias-apenanti-stin-texniti-noimosyni/"

# Extract with enhanced Selenium (for JavaScript sites)
python manage.py process_article "https://www.amna.gr/home/article/907263/Chrimatistirio-Se-nea-upsila-15-eton-i-agora-me-othisi-apo-to-deal-tis-Alpha-Unicredit" --enhanced

# Full processing with AI analysis (6 agents)
python manage.py process_article "https://www.amna.gr/home/article/907263/Chrimatistirio-Se-nea-upsila-15-eton-i-agora-me-othisi-apo-to-deal-tis-Alpha-Unicredit" --analyze

# Enhanced extraction + AI analysis (recommended for JS sites)
python manage.py process_article "https://www.amna.gr/home/article/907263/Chrimatistirio-Se-nea-upsila-15-eton-i-agora-me-othisi-apo-to-deal-tis-Alpha-Unicredit" --enhanced --analyze
```

### Supported Greek News Sites
```bash
# Major news sites (basic extraction)
python manage.py process_article "https://www.kathimerini.gr/..." --analyze
python manage.py process_article "https://www.tanea.gr/..." --analyze
python manage.py process_article "https://www.protothema.gr/..." --analyze

# JavaScript-heavy sites (use --enhanced)
python manage.py process_article "https://www.amna.gr/..." --enhanced --analyze
python manage.py process_article "https://www.cnn.gr/..." --enhanced --analyze
python manage.py process_article "https://www.skai.gr/..." --enhanced --analyze
```

## Troubleshooting

### Migration Issues
```bash
# If you encounter "relation does not exist" errors:
python manage.py migrate --run-syncdb

# For "multiple values for keyword argument" in ProcessingJob:
python manage.py migrate news_aggregator 0002_processing_job_nullable_article

# Complete migration reset (if needed):
python manage.py migrate news_aggregator zero
python manage.py migrate

# Fix migration dependencies:
python fix_migrations.py
```

### Chrome WebDriver Issues
```bash
# If Selenium fails with Chrome version mismatch:
# The enhanced extractor will automatically fallback to regular Chrome
# Or install specific ChromeDriver version:
pip install --upgrade webdriver-manager

# For "session not created" errors:
# The system will auto-fallback from undetected-chromedriver to regular Chrome
```

### Agent Errors
```bash
# "COMPLEX" error - Fixed by updating ComplexityLevel enum usage
# "multiple values for search_params" - Fixed in GrokClient

# Test agents independently:
python test_agent_coordinator.py

# Test specific fixes:
python quick_test_viewpoints.py
```

### Unicode/Greek Text Issues
```bash
# For Windows encoding errors with Greek text:
# Set console to UTF-8:
chcp 65001

# Or set environment variable:
set PYTHONIOENCODING=utf-8
```

### Database Connection
```bash
# SQLite (default for development):
# No setup needed, automatically created as db.sqlite3

# PostgreSQL (production):
createdb news_copilot_dev
# Update DATABASE_URL in .env
```

## Access Points
- **Django Backend**: http://localhost:8000
- **Django Admin**: http://localhost:8000/admin/
- **API Endpoints**: http://localhost:8000/api/
- **Frontend Next.js**: http://localhost:3000
- **API Documentation**: http://localhost:8000/api/docs/ (if configured)

## Quick Test Commands
```bash
# Test extraction is working:
python manage.py process_article "https://www.kathimerini.gr/economy/562917774/i-agora-ergasias-apenanti-stin-texniti-noimosyni/"

# Test AI agents are working:
python test_agent_coordinator.py

# Django shell for debugging:
python manage.py shell

# Check database tables:
python manage.py dbshell
```