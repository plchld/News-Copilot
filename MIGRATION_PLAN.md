# News Copilot Migration Plan

## Overview
This document outlines the step-by-step migration from the current architecture to a Django + Next.js full-stack application.

## Current State
- Flask API in `deprecated_v1/api/`
- Standalone news aggregator in `news-aggregator/`
- Agent system with AI analysis capabilities
- PostgreSQL (5499) and MongoDB (27099) running in Docker

## Target Architecture
- **Backend**: Django REST API with Celery workers
- **Frontend**: Next.js 15 with TypeScript
- **Databases**: PostgreSQL (primary) + MongoDB (document store)
- **Task Queue**: Celery + Redis
- **AI Processing**: Integrated Django management commands

## Migration Phases

### Phase 1: Backend Setup ✅
- [x] Create Django project structure
- [x] Configure settings (base, development, production)
- [x] Set up core apps (authentication, core, news_aggregator, api)
- [x] Create base models (User, Article, AIAnalysis)
- [x] Configure JWT authentication

### Phase 2: Code Migration (Current)
- [ ] Migrate agents from `news-aggregator/agents/` to Django
- [ ] Migrate processors to Django management commands
- [ ] Create Django serializers for API responses
- [ ] Set up Celery tasks for background processing
- [ ] Migrate existing API endpoints to Django views

### Phase 3: Frontend Development
- [ ] Initialize Next.js 15 with TypeScript
- [ ] Set up API client with axios/fetch
- [ ] Create authentication flow (JWT)
- [ ] Migrate existing UI components
- [ ] Implement real-time updates (SSE/WebSockets)

### Phase 4: Integration
- [ ] Connect frontend to Django API
- [ ] Set up CORS properly
- [ ] Configure nginx reverse proxy
- [ ] Test end-to-end functionality
- [ ] Migrate existing data

### Phase 5: Deployment Preparation
- [ ] Create production configurations
- [ ] Set up CI/CD pipeline
- [ ] Document deployment process
- [ ] Create migration scripts for data

## File Mapping

### Agents Migration
```
news-aggregator/agents/ → backend/apps/news_aggregator/agents/
├── base_agent.py → base.py
├── *_agent.py → [keep same names]
├── schemas.py → schemas.py
└── news_agent_coordinator.py → coordinator.py
```

### API Endpoints Migration
```
deprecated_v1/api/routes/ → backend/apps/api/views/
├── analysis.py → news_views.py
├── auth.py → [use authentication app]
└── unified_analysis.py → analysis_views.py
```

### Processors Migration
```
news-aggregator/processors/ → backend/apps/news_aggregator/
├── article_processor.py → extractors/article.py
├── ai_enrichment.py → tasks/enrichment.py
└── enhanced_extractor.py → extractors/selenium.py
```

## Next Steps

1. **Immediate Tasks**:
   - Create management command for article processing
   - Set up Celery tasks for AI analysis
   - Create API serializers and viewsets
   - Initialize Next.js frontend

2. **Testing Strategy**:
   - Unit tests for each Django app
   - Integration tests for API endpoints
   - E2E tests with Cypress/Playwright
   - Performance testing for AI pipeline

3. **Data Migration**:
   - Export existing articles from file system
   - Import into PostgreSQL
   - Maintain backward compatibility during transition

## Commands Reference

### Django Development
```bash
# Backend development
cd backend
python manage.py runserver

# Create migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run tests
python manage.py test
```

### Celery Workers
```bash
# Start worker
celery -A config worker -l info

# Start beat scheduler
celery -A config beat -l info

# Monitor tasks
celery -A config flower
```

### Frontend Development
```bash
# Frontend development
cd frontend
pnpm run dev

# Build for production
pnpm run build

# Type checking
pnpm run type-check
```

## Environment Variables

Add to `.env`:
```
# Django
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000/api

# Redis (for Celery)
REDIS_URL=redis://localhost:6379/0
```

## Notes
- Keep the existing system running during migration
- Test each component independently before integration
- Document API changes for frontend team
- Maintain data integrity during migration