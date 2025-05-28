# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Architecture

News Copilot is a Greek news intelligence platform with AI-powered contextual analysis. The system consists of:

**Frontend**: Next.js TypeScript application (`frontend/`) with modern React components and real-time analysis UI
**Backend**: Django 5.0+ backend (`backend/`) with modular app structure, REST API, and advanced agent system
**Legacy System**: Deprecated Flask API (`deprecated_v1/`) and news aggregator (`news-aggregator/`) 
**Authentication**: Supabase-based auth system with JWT tokens, magic links, and user tiers
**Content Processing**: Enhanced Selenium-based extraction supporting 50+ Greek news sites including JavaScript-heavy sites

The new architecture uses Django REST Framework with async support, Celery for background tasks, and an advanced agent coordination system.

### Django Backend Structure (`backend/`)
The Django backend is organized into modular apps:

**Core Structure**:
- **config/**: Django settings with modular configuration (base, development, production)
- **apps/core/**: Base models, authentication, and common utilities
- **apps/news_aggregator/**: Main news processing and article management
- **apps/api/**: REST API endpoints and serializers
- **apps/authentication/**: Enhanced user management and JWT integration

**News Aggregator App** (`apps/news_aggregator/`):
- **models.py**: Article, NewsSource, ProcessingJob, AIAnalysis models
- **extractors/**: Enhanced article extraction with Selenium support
  - `article.py` - Basic and enhanced extractors with JavaScript support
- **agents/**: Advanced AI agent system
  - `coordinator.py` - AgentCoordinator for parallel execution
  - `base.py` - BaseAgent, AnalysisAgent classes with async support
  - Individual specialized agents (jargon, viewpoints, fact_check, bias, timeline, expert)
- **management/commands/**: Django management commands
  - `process_article.py` - Article extraction and analysis
  - `test_extraction.py` - Testing utilities
- **tasks.py**: Celery background tasks
- **grok_client.py**: Enhanced Grok API integration

**Enhanced Article Extraction**:
- **Selenium WebDriver**: Undetected ChromeDriver for JavaScript sites
- **AMNA.gr Support**: Special Angular handling with extended wait times
- **Greek News Sites**: Enhanced selectors for 50+ sites
- **Auto-detection**: Intelligent fallback for JavaScript-heavy sites

**Agent Intelligence System**:
- **Parallel Execution**: Concurrent agent processing with semaphore control
- **Dynamic Model Selection**: Grok-3-mini/Grok-3 based on complexity
- **Search Integration**: Live search for fact-checking and viewpoints
- **Greek Language**: All prompts and responses optimized for Greek content
- **Structured Outputs**: JSON schemas for consistent data exchange

## Development Commands

### Quick Start (Django Backend)
```bash
# 1. Backend Setup
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env  # Edit with your API keys

# Database setup (PostgreSQL recommended)
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start Django development server
python manage.py runserver 8000
```

### Frontend Setup (Next.js)
```bash
# 2. Frontend Setup
cd frontend

# Install Node.js dependencies
npm install

# Set up environment variables
cp .env.example .env.local  # Edit with API endpoints

# Start Next.js development server
npm run dev  # Runs on :3000
```

### Backend Development (Django)
```bash
# Navigate to backend directory
cd backend

# Database operations
python manage.py makemigrations
python manage.py migrate
python manage.py showmigrations

# Article processing
python manage.py process_article <article_url>                    # Basic extraction
python manage.py process_article <article_url> --enhanced         # With Selenium
python manage.py process_article <article_url> --analyze          # With AI analysis
python manage.py process_article <article_url> --enhanced --analyze  # Full processing

# Test extraction specifically for AMNA.gr and JavaScript sites
python manage.py process_article "https://www.amna.gr/home/article/..." --enhanced --analyze

# Agent system testing
python test_agent_coordinator.py   # Test all agents
python quick_test_viewpoints.py   # Test specific fixes

# Django shell for debugging
python manage.py shell

# Celery background tasks (if configured)
celery -A config worker --loglevel=info
celery -A config beat --loglevel=info
```

### Enhanced Article Extraction
```bash
# Test enhanced extractor with JavaScript sites
python manage.py process_article "https://www.amna.gr/..." --enhanced
python manage.py process_article "https://www.cnn.gr/..." --enhanced
python manage.py process_article "https://www.skai.gr/..." --enhanced

# Full pipeline with AI analysis
python manage.py process_article "https://www.amna.gr/..." --enhanced --analyze

# Test individual agents
cd backend
python -c "
import asyncio
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.news_aggregator.agents.coordinator import AgentCoordinator

async def test():
    coordinator = AgentCoordinator()
    results = await coordinator.analyze_article('Test Greek article content')
    print(f'Analysis completed: {len(results)} agents')

asyncio.run(test())
"
```

### Legacy Development (Deprecated)
```bash
# Legacy Flask API (deprecated_v1/)
cd deprecated_v1
python api/index.py

# Legacy news aggregator (news-aggregator/)
cd news-aggregator
python web_app.py

# These are maintained for reference but new development uses Django backend
```

### Testing
```bash
# Backend tests
cd backend
python manage.py test
python -m pytest  # If pytest is configured

# Test individual components
python test_enhanced_extractor.py  # Test extraction logic
python test_agent_coordinator.py   # Test AI agents

# Frontend tests
cd frontend
npm test
npm run type-check
npm run lint
```

### Database Management
```bash
# PostgreSQL setup (recommended)
# Install PostgreSQL and create database
createdb news_copilot_dev

# Update backend/.env with database settings
DATABASE_URL=postgresql://username:password@localhost:5432/news_copilot_dev

# Run migrations
python manage.py migrate

# Optional: Load sample data
python manage.py loaddata fixtures/sample_data.json  # If available
```

## Key Technical Details

### Django Backend Configuration
- **Django 5.0+**: Modern Django with async support and modular settings
- **Database**: PostgreSQL (primary) with MongoDB support via pymongo
- **Background Tasks**: Celery with Redis broker for article processing
- **API**: Django REST Framework with JWT authentication
- **Testing**: Django TestCase and pytest integration

### Enhanced Article Extraction
- **Selenium WebDriver**: Undetected ChromeDriver with auto-fallback to regular Chrome
- **JavaScript Support**: Special handling for Angular sites (AMNA.gr), React apps (CNN.gr)
- **Greek News Sites**: Enhanced selectors for 50+ sites with auto-detection
- **Content Processing**: Multi-tier fallback (trafilatura → BeautifulSoup → Selenium)
- **Performance**: Intelligent caching and resource cleanup

### Agent Intelligence System
- **Grok API Integration**: XAI_API_KEY with live search capabilities
- **6 Specialized Agents**:
  - **JargonAgent**: Technical term explanations (grok-3-mini)
  - **ViewpointsAgent**: Alternative perspectives with live search (grok-3)
  - **FactCheckAgent**: Claim verification with search (grok-3)
  - **BiasAgent**: Greek political spectrum analysis (grok-3)
  - **TimelineAgent**: Event chronology (grok-3)
  - **ExpertAgent**: Expert opinions with search (grok-3)
- **Parallel Execution**: Concurrent processing with semaphore control
- **Error Handling**: Comprehensive retry logic and graceful degradation
- **Unicode Support**: Proper Greek character handling on Windows/Linux

### Authentication & Database
- **Supabase Integration**: JWT tokens, magic links, user tiers
- **Models**: Article, NewsSource, ProcessingJob, AIAnalysis with UUID primary keys
- **Rate Limiting**: Tier-based analysis limits (free: 10/month, premium: 50/month, admin: unlimited)
- **Database Schema**: PostgreSQL with proper indexing and foreign key constraints

### API Architecture
- **Django REST Framework**: Modern API with serializers and viewsets
- **Async Support**: Mixed sync/async operations with proper context handling
- **Management Commands**: CLI tools for article processing and testing
- **Background Tasks**: Celery integration for scalable processing

### Prompt System
The prompt system follows a standardized architecture (see `PROMPT_ARCHITECTURE.md`):

**Core Components**:
- `prompt_utils.py`: Centralized prompt utilities with SYSTEM_PREFIX and TRUST_GUARDRAILS
- Task instruction generators for each analysis type
- Automatic inclusion of scratchpad technique for reasoning
- Support for conversation-based refinement

**All agents now use**:
- Proper prompt utilities from `prompt_utils.py`
- Centralized search parameter builders with domain exclusion
- Conversation history for iterative refinement
- Consistent Greek output requirements

### Web App Architecture (Next.js)
The `web/` directory contains a modern Next.js application:
- **src/app/**: App Router with layout.tsx and page.tsx
- **src/components/**: React components organized by feature
  - `analysis/` - Analysis result components (BiasAnalysis, FactCheckAnalysis, etc.)
  - `AnalysisContent.tsx` - Main analysis display
  - `ArticleInput.tsx` - URL input component
  - `LoadingSpinner.tsx` - Progress indication
- **src/hooks/**: Custom React hooks (useProgressSequence.ts)
- **src/utils/**: Utility functions (markdown.ts)
- **Styling**: Tailwind CSS with custom configurations

### Chrome Extension Structure (Deprecated)
Extension moved to `deprecated/extension/`:
- **manifest.json**: Configured for 50+ Greek news sites
- **content_script_clean.js**: Sidebar UI implementation
- **popup-auth.html/js**: Authentication interface
- **Note**: Extension functionality migrated to Next.js web app

## Supported Sites

The extension supports 50+ Greek news sites across categories:
- **Major News**: kathimerini.gr, tanea.gr, protothema.gr, skai.gr, tovima.gr, ethnos.gr
- **Business**: naftemporiki.gr, capital.gr
- **Digital**: iefimerida.gr, newsbeast.gr, cnn.gr, ant1news.gr, in.gr, news247.gr
- **Alternative**: efsyn.gr, avgi.gr, documento.gr, liberal.gr, thetoc.gr
- **Regional**: makthes.gr, real.gr, star.gr

Site configuration is automatically tested with `test_sites.py` for accessibility validation.

## Configuration Requirements

### Environment Variables (backend/.env)
```bash
# Django Configuration
SECRET_KEY=your-django-secret-key
DEBUG=True
DJANGO_SETTINGS_MODULE=config.settings.development

# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/news_copilot_dev
# Alternative: SQLite for development
# DATABASE_URL=sqlite:///db.sqlite3

# API Keys
XAI_API_KEY=your-grok-api-key

# Supabase Authentication
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key

# Redis (for Celery, optional)
REDIS_URL=redis://localhost:6379/0

# Optional Settings
AUTH_ENABLED=True
EXCLUDED_DOMAINS=example.com,spam-site.com
```

### Frontend Environment Variables (frontend/.env.local)
```bash
# API Endpoints
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

### Dependencies Installation
```bash
# Backend Dependencies (Python 3.10+)
cd backend
pip install -r requirements.txt

# Key packages included:
# - Django>=5.0,<6.0
# - djangorestframework
# - djangorestframework-simplejwt
# - psycopg[binary]  # PostgreSQL
# - celery[redis]    # Background tasks
# - selenium
# - undetected-chromedriver
# - trafilatura
# - beautifulsoup4
# - httpx
# - pydantic

# Frontend Dependencies (Node.js 18+)
cd frontend
npm install

# Key packages included:
# - Next.js 15
# - React 18
# - TypeScript
# - Tailwind CSS
# - Supabase client
```

### Extension Permissions
- `activeTab`: Access to current tab content
- `scripting`: Content script injection
- `nativeMessaging`: Future integration capability
- `storage`: Local storage for auth tokens
- `http://localhost:8080/*`: Local backend API communication
- `https://*.supabase.co/*`: Supabase authentication
- `https://news-copilot.vercel.app/*`: Production API

## Development Workflow

### Adding New Analysis Types (Django)
1. **Create Agent Class**: Add new agent in `backend/apps/news_aggregator/agents/`
   ```python
   # my_new_agent.py
   from .base import AnalysisAgent, AgentConfig, ModelType, ComplexityLevel
   
   class MyNewAgent(AnalysisAgent):
       def __init__(self):
           config = AgentConfig(
               name="my_new_analysis",
               description="Description of analysis",
               default_model=ModelType.GROK_3,
               complexity=ComplexityLevel.MEDIUM
           )
           schema = get_my_new_response_schema()
           super().__init__(config, schema)
   ```

2. **Add Schema**: Define JSON schema in `schemas.py`
3. **Register Agent**: Add to `AgentCoordinator` in `coordinator.py`
4. **Update Frontend**: Add component in `frontend/src/components/analysis/`
5. **Test**: Use `python manage.py process_article <url> --analyze`

### Adding New Supported Sites
1. **Update NewsSource**: Add domain to database with `requires_javascript` flag
   ```python
   # In Django shell
   from apps.news_aggregator.models import NewsSource
   NewsSource.objects.create(
       name="New Site",
       domain="newsite.gr", 
       requires_javascript=True  # If it's a JS-heavy site
   )
   ```

2. **Test Extraction**: 
   ```bash
   python manage.py process_article "https://newsite.gr/article" --enhanced
   ```

3. **Update Documentation**: Add to `SUPPORTED_SITES.md`

### Modifying Article Extraction
- **Basic Sites**: Modify selectors in `ArticleExtractor` class
- **JavaScript Sites**: Enhance `EnhancedArticleExtractor` with new selectors
- **Special Cases**: Add domain-specific handling like AMNA.gr Angular support
- **Testing**: Use `--enhanced` flag for JavaScript sites

### Agent System Development
- **Prompts**: All prompts in Greek, stored in agent classes
- **Search Integration**: Use `search_enabled=True` or custom `search_params`
- **Model Selection**: Choose grok-3-mini for simple tasks, grok-3 for complex
- **Testing**: Run `python test_agent_coordinator.py`

## Deployment Details

### Django Production Deployment
```bash
# 1. Prepare for production
cd backend

# Set production environment
export DJANGO_SETTINGS_MODULE=config.settings.production
export DEBUG=False

# Collect static files
python manage.py collectstatic --noinput

# Run database migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start with Gunicorn (recommended)
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

### Frontend Production Deployment
```bash
# Build Next.js application
cd frontend
npm run build
npm start  # or use a process manager like PM2
```

### Docker Deployment (Optional)
```bash
# Build and run with Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# Or individual containers
docker build -t news-copilot-backend ./backend
docker build -t news-copilot-frontend ./frontend
```

### Legacy Vercel Deployment (Deprecated)
- **Entry Point**: `deprecated_v1/api/index.py` (no longer maintained)
- **New Recommendation**: Use Django deployment on cloud platforms
- **Alternatives**: Railway, DigitalOcean App Platform, AWS ECS, Google Cloud Run

### Database Setup
- **PostgreSQL**: Recommended for production
- **Supabase**: Complete setup guide in `SUPABASE_SETUP.md`
- **Schema**: Run migrations with `python manage.py migrate`
- **Admin Setup**: Use Django admin or management commands

## Code Quality & Formatting
The project uses standardized formatting and linting:
- **Python**: Black (88 char line length), Ruff linting, type hints
- **TypeScript**: Prettier formatting, ESLint, strict TypeScript config
- **Testing**: Pytest with coverage reporting, organized test structure
- **CI/CD**: Automated via Makefile commands

## Development Notes

### Key Features of Django Backend
- **Enhanced Article Extraction**: Selenium WebDriver with AMNA.gr Angular support
- **6 AI Agents**: Parallel processing with Grok API integration
- **Greek Language**: Full Unicode support, optimized for Greek content
- **Async Support**: Mixed sync/async operations for optimal performance
- **Rate Limiting**: User tier system (free/premium/admin) with database tracking
- **Management Commands**: CLI tools for article processing and testing

### Migration from Legacy System
- **From Flask to Django**: Improved structure, better ORM, built-in admin
- **Enhanced Extraction**: Migrated sophisticated Selenium logic from news-aggregator
- **Agent System**: Upgraded coordinator with better error handling and parallel execution
- **Database**: PostgreSQL with proper models, migrations, and constraints
- **Frontend**: Modern Next.js TypeScript application

### Special Handling
- **JavaScript Sites**: Auto-detection and enhanced extraction for sites like AMNA.gr
- **Greek Content**: Proper Unicode handling, Greek-specific content cleaning
- **Chrome WebDriver**: Version compatibility handling, undetected ChromeDriver integration
- **Agent Coordination**: Search parameter handling, model selection, parallel execution

### Testing & Debugging
- **Management Commands**: `process_article`, `test_extraction` for development
- **Agent Testing**: `test_agent_coordinator.py` for comprehensive agent testing
- **Enhanced Logging**: Proper Unicode logging, detailed error messages
- **Development Tools**: Django admin, shell, debug toolbar