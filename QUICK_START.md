# Quick Start Guide

## Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL (or Docker)

## Installation Options

### Option 1: Minimal Setup (Fastest)
```bash
# Backend - minimal dependencies
cd backend
pip install -r requirements-minimal.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

# Frontend - in new terminal
cd frontend
pnpm install
pnpm run dev
```

### Option 2: Full Setup (Recommended)
```bash
# Start databases first
docker-compose up -d

# Backend
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

# Frontend - in new terminal
cd frontend
pnpm install
pnpm run dev
```

### Option 3: Using Make
```bash
# Everything at once
make setup
make run-api  # Terminal 1
make run-web  # Terminal 2
```

## Troubleshooting

### Dependency Conflicts
If you get dependency conflicts, try:
```bash
# Create fresh virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install minimal first
pip install -r requirements-minimal.txt

# Then add other packages as needed
pip install celery[redis]
pip install trafilatura selenium beautifulsoup4
```

### Database Issues
- PostgreSQL not needed for minimal setup (uses SQLite)
- MongoDB is optional (for document storage)
- Update `.env` with your database credentials

### Missing Packages
Some packages are optional:
- `undetected-chromedriver`: Install separately if needed
- `django-debug-toolbar`: Only for development
- AI packages: Add when implementing AI features

## Access Points
- API: http://localhost:8000
- API Docs: http://localhost:8000/api/docs/
- Frontend: http://localhost:3000
- Django Admin: http://localhost:8000/admin/