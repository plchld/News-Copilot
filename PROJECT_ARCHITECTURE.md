# News Copilot - Full Stack Architecture

## Overview
News Copilot is a comprehensive news intelligence platform built with Django (backend) and Next.js (frontend), featuring AI-powered analysis and real-time news aggregation.

## Directory Structure
```
News-Copilot/
├── backend/                    # Django backend
│   ├── config/                # Django settings & URLs
│   ├── apps/                  # Django applications
│   │   ├── core/             # Core utilities and base models
│   │   ├── authentication/   # User auth & JWT management
│   │   ├── news_aggregator/  # News collection & processing
│   │   └── api/              # REST API endpoints
│   ├── requirements/          # Python dependencies
│   └── manage.py
│
├── frontend/                  # Next.js 15 TypeScript
│   ├── src/
│   │   ├── app/              # App router pages
│   │   ├── components/       # React components
│   │   ├── lib/              # Utilities & API clients
│   │   └── types/            # TypeScript definitions
│   ├── public/
│   └── package.json
│
├── services/                  # Microservices & workers
│   ├── celery/               # Background task workers
│   ├── scrapers/             # News scraping services
│   └── ai_pipeline/          # AI processing pipeline
│
├── docker/                    # Docker configurations
│   ├── django/
│   ├── nextjs/
│   ├── nginx/
│   └── redis/
│
├── deprecated_v1/             # Legacy system
├── news-aggregator/           # Current v2 (to be migrated)
└── docker-compose.yml         # Full stack orchestration
```

## Technology Stack

### Backend (Django)
- **Framework**: Django 5.2 with async support
- **API**: Django REST Framework
- **Task Queue**: Celery + Redis
- **Database**: PostgreSQL (primary) + MongoDB (document store)
- **Authentication**: JWT with django-rest-knox
- **AI Integration**: Direct Python integration with Grok API

### Frontend (Next.js)
- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS + shadcn/ui
- **State Management**: React Query + Zustand
- **Real-time**: Server-Sent Events / WebSockets

### Infrastructure
- **Reverse Proxy**: Nginx
- **Container Orchestration**: Docker Compose
- **Background Jobs**: Celery + Redis
- **Search**: PostgreSQL Full-Text / Elasticsearch (future)

## API Architecture

### REST Endpoints
```
/api/v1/
├── auth/
│   ├── login/
│   ├── logout/
│   ├── refresh/
│   └── profile/
├── news/
│   ├── articles/
│   ├── sources/
│   ├── process/
│   └── search/
├── analysis/
│   ├── analyze/
│   ├── agents/
│   └── results/{id}/
└── admin/
    ├── users/
    └── stats/
```

### WebSocket Events
```
ws://localhost:8000/ws/
├── news/updates/
├── analysis/progress/
└── notifications/
```

## Development Workflow

### Local Development
```bash
# Backend
cd backend
pip install -r requirements.txt
python manage.py runserver

# migrations and others
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser

# Frontend  
cd frontend
pnpm install
pnpm run dev

# Full stack with Docker
docker-compose up
```

### Task Queue
```bash
# Start Celery worker
celery -A config worker -l info

# Start Celery beat (scheduler)
celery -A config beat -l info
```

## Deployment Strategy

### Production Architecture
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Vercel    │     │  AWS ALB    │     │   AWS ECS   │
│  (Next.js)  │────▶│   (Nginx)   │────▶│  (Django)   │
└─────────────┘     └─────────────┘     └─────────────┘
                            │                     │
                            ▼                     ▼
                    ┌─────────────┐     ┌─────────────┐
                    │    Redis    │     │  PostgreSQL │
                    │  ElastiCache│     │     RDS     │
                    └─────────────┘     └─────────────┘
```

### Scaling Considerations
- Django: Horizontal scaling with ECS/Kubernetes
- Next.js: Edge deployment on Vercel
- Background Jobs: Separate Celery worker pools
- Database: Read replicas for heavy queries
- Caching: Redis for session & API caching