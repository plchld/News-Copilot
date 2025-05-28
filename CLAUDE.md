# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Architecture

News Copilot is a Greek news intelligence platform with AI-powered contextual analysis. The system consists of:

**Frontend**: Chrome extension (`extension/`) with progressive sidebar UI that provides non-intrusive article analysis
**Backend**: Python Flask API deployed on Vercel (`api/index.py`) with Grok AI integration for live search and structured analysis
**Authentication**: Supabase-based auth system with magic links, JWT tokens, and rate limiting
**Content Processing**: Trafilatura-based article extraction supporting 50+ Greek news sites

The architecture uses Server-Sent Events (SSE) for real-time progress updates and structured JSON schemas for AI responses.

### Backend API Structure
The API is modularly organized in the `api/` directory:
- **index.py**: Vercel entry point that imports the Flask app
- **app.py**: Flask application factory with route registration
- **routes/**: Modular route handlers (analysis.py, auth.py, admin.py)
- **core/**: Core processing logic (analysis_handlers.py, article_extractor.py, grok_client.py)
- **auth/**: Authentication system (supabase.py, decorators.py, models.py)
- **utils/**: Utility modules (prompt_utils.py, search_params_builder.py, thinking_utils.py)
- **config.py**: Configuration management for all services
- **models.py**: Pydantic models for request/response validation

### Agentic Intelligence Architecture
The `api/agents/` directory implements a sophisticated agent-based system:
- **base_agent.py**: Base classes (BaseAgent, AnalysisAgent, NestedAgent) with dynamic model selection
- **optimized_coordinator.py**: AgentCoordinator orchestrates parallel execution and quality control
- **schemas.py**: Structured output schemas for all agent responses
- **Individual agents**:
  - `jargon_agent.py` - Term explanations (grok-3-mini for cost efficiency)
  - `viewpoints_agent.py` - Alternative perspectives (grok-3)
  - `fact_check_agent.py` - Claim verification (grok-3)
  - `bias_agent.py` - Greek political spectrum analysis (grok-3)
  - `timeline_agent.py` - Event chronology (grok-3)
  - `expert_agent.py` - Expert opinions (grok-3)
  - `x_pulse_agent.py` - X discourse analysis with 5 nested sub-agents (grok-3)
  - `perspective_enricher.py` - Additional perspective enhancement
- **Advanced features**:
  - Dynamic model selection based on user tier, article length, and retry count
  - Parallel execution for 3x faster analysis
  - Quality control with chat-based refinement
  - Cost optimization through strategic model usage
  - Structured JSON schemas for all outputs

## Development Commands

### Quick Start
```bash
# Setup environment and install all dependencies
make install && make setup-env

# Start both API and web servers (mirrors Vercel deployment)
make run

# Individual server commands
make run-api    # Flask API on :8080
make run-web    # Next.js web on :3000
```

### Development Workflow
```bash
# Format and lint code
make format     # Black + Prettier formatting
make lint       # Flake8 + ESLint linting

# Testing commands
make test              # Run all tests with coverage
make test-unit         # Unit tests only
make test-integration  # Integration tests only
make test-sites        # Test news site extraction

# Specific test commands
python run_tests.py tests/test_routes.py::TestRoutes::test_home_api_request
pytest -m "not slow"   # Skip slow tests
pytest -m unit         # Run only unit tests

# Debug and analyze
make debug-grok        # Debug Grok API connection
make analyze          # Interactive URL analysis
make test-api         # Test API health endpoints
```

### Backend Development
```bash
# Direct API server start
python api/index.py

# Development server (with hot reload)
python dev_server.py

# Legacy CLI mode (deprecated)
python explain_with_grok.py <article_url>

# Authentication testing
python test_auth_system.py
python setup_admin.py  # Create admin user

# Agent system testing
python debug/debug_agents.py
python debug/test_viewpoints_debug.py
```

### Web App Development
```bash
# Next.js development (from web/ directory)
cd web && npm run dev
cd web && npm run build
cd web && npm run type-check
cd web && npm run lint
```

### Test Infrastructure
The project uses pytest with the following structure:
- **tests/**: Main test directory with organized test modules
- **conftest.py**: Pytest configuration and shared fixtures
- **pytest.ini**: Test runner configuration
- **run_tests.py**: Main test runner with coverage reporting

## Key Technical Details

### API Integration
- **Grok API**: Uses XAI_API_KEY with live search enabled via `search_parameters`
- **Response Formats**: JSON schemas for structured data (jargon, fact-check, bias, timeline, expert opinions)
- **Error Handling**: Comprehensive APIStatusError and connection error handling

### Authentication System (Supabase)
- **Magic Link Auth**: Email-based authentication without passwords
- **JWT Tokens**: Secure token validation using PyJWT
- **Rate Limiting**: 10 free analyses/month, 50 for premium, unlimited for admin
- **User Tiers**: free, premium, admin with different rate limits
- **Database Schema**: See `supabase_schema.sql` for complete structure

### Content Processing
- **Article Extraction**: Trafilatura with fallback mechanisms for complex sites
- **Greek Language**: All prompts and responses in Greek with proper Unicode handling
- **Citation Tracking**: Automatic source verification and URL validation

### API Endpoints
- **Auth Routes**: `/api/auth/login`, `/api/auth/profile`, `/api/auth/logout`
- **Analysis Routes**: `/augment`, `/augment-stream`, `/deep-analysis`
- **Admin Routes**: `/api/admin/*` (requires admin auth)
- **CORS Setup**: Configured for Vercel deployment and localhost:8080

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

### Environment Variables
- `XAI_API_KEY`: Required for Grok AI API access
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_ANON_KEY`: Public Supabase key for client access
- `SUPABASE_SERVICE_KEY`: Service role key for admin operations
- `BASE_URL`: API base URL (https://news-copilot.vercel.app for production)
- `FLASK_PORT`: Optional, defaults to 8080 for local dev
- `DEBUG_MODE`: Optional development flag
- `AUTH_ENABLED`: Optional flag to enable/disable authentication (defaults to true)

### Extension Permissions
- `activeTab`: Access to current tab content
- `scripting`: Content script injection
- `nativeMessaging`: Future integration capability
- `storage`: Local storage for auth tokens
- `http://localhost:8080/*`: Local backend API communication
- `https://*.supabase.co/*`: Supabase authentication
- `https://news-copilot.vercel.app/*`: Production API

## Development Workflow

When adding new analysis types:
1. Add prompt to `prompts.py` with Greek instructions
2. Define JSON schema in `get_deep_analysis()` function
3. Add to `prompt_map` and `schema_map` dictionaries
4. Update frontend to handle new analysis type

When adding new supported sites:
1. Add domain pattern to `manifest.json` content_scripts.matches
2. Test extraction with `python test_sites.py`
3. Update `SUPPORTED_SITES.md` documentation

When modifying AI prompts:
- Ensure all responses are in Greek
- Include @username references for X/Twitter content
- Validate JSON schema compatibility
- Test with live search enabled

When deploying to production:
1. Ensure all environment variables are set in Vercel
2. Test authentication flow with `test_auth_system.py`
3. Verify Supabase RLS policies are active
4. Update extension to use production API URL

## Deployment Details

### Vercel Deployment
- **Entry Point**: `api/index.py` handles all routes
- **Build Config**: See `vercel.json` for Lambda configuration
- **Environment**: Set all required env vars in Vercel dashboard
- **Domain**: Configure custom domain or use default .vercel.app
- **Static Files**: Verification pages served from `static/` directory

### Supabase Setup
- **Documentation**: Complete setup guide in `SUPABASE_SETUP.md`
- **Schema**: Run `supabase_schema.sql` to create tables and RLS policies
- **Email Templates**: Configure in Supabase dashboard for magic links
- **Admin Setup**: Use `setup_admin.py` to create initial admin user
- **Verification Pages**: `static/verification-success.html` and `static/verification-failed.html`

## Code Quality & Formatting
The project uses standardized formatting and linting:
- **Python**: Black (88 char line length), Ruff linting, type hints
- **TypeScript**: Prettier formatting, ESLint, strict TypeScript config
- **Testing**: Pytest with coverage reporting, organized test structure
- **CI/CD**: Automated via Makefile commands

## Development Notes
- **Environment Setup**: Use `make setup-env` to create .env with required variables
- **Dual Architecture**: Web app (Next.js) + API (Flask) mirrors Vercel deployment
- **Debug Tools**: Comprehensive debugging in `debug/` directory for API issues
- **Greek Language**: All user-facing content and AI responses in Greek
- **Rate Limiting**: Built-in user tier system (free/premium/admin)
- **Structured Outputs**: All AI agents return validated JSON schemas