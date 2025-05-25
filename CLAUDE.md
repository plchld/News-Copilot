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
- **routes.py**: Main API routes for analysis endpoints
- **analysis_handlers.py**: Core analysis processing logic
- **article_extractor.py**: Content extraction with Trafilatura
- **grok_client.py**: Grok API client wrapper with error handling
- **config.py**: Configuration management for all services
- **models.py**: Pydantic models for request/response validation
- **auth modules**: Multiple auth implementations (supabase_auth.py, http_supabase.py, simple_auth.py)

### Agentic Intelligence Architecture (NEW)
The `api/agents/` directory implements a sophisticated agent-based system:
- **base_agent.py**: Base classes (BaseAgent, AnalysisAgent, NestedAgent) with dynamic model selection
- **coordinator.py**: AgentCoordinator orchestrates parallel execution and quality control
- **Individual agents**:
  - `jargon_agent.py` - Term explanations (grok-3-mini for cost efficiency)
  - `viewpoints_agent.py` - Alternative perspectives (grok-3)
  - `fact_check_agent.py` - Claim verification (grok-3)
  - `bias_agent.py` - Greek political spectrum analysis (grok-3)
  - `timeline_agent.py` - Event chronology (grok-3)
  - `expert_agent.py` - Expert opinions (grok-3)
  - `x_pulse_agent.py` - X discourse analysis with 5 nested sub-agents (grok-3)
- **Advanced features**:
  - Dynamic model selection based on user tier, article length, and retry count
  - Parallel execution for 3x faster analysis
  - Quality control with chat-based refinement
  - Cost optimization through strategic model usage

## Development Commands

### Backend Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env  # Then edit with your keys
# Required: XAI_API_KEY, SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY

# Start local development server
python explain_with_grok.py --server

# CLI testing mode
python explain_with_grok.py <article_url>

# Test authentication system
python test_auth_system.py

# Test Supabase integration
python test_supabase_simple.py
python test_http_supabase.py

# Test agentic architecture
python api/agents/test_agents.py
```

### Chrome Extension Development
```bash
# Load extension in Chrome
# 1. Open chrome://extensions/
# 2. Enable Developer mode
# 3. Click "Load unpacked" and select extension/ folder

# Test on Greek news sites
# Visit any supported site from manifest.json matches[]
# Extension uses popup-auth.html for auth
```

### Testing
```bash
# Run all tests with coverage
python run_tests.py
# or
pytest --cov=api --cov-report=term-missing

# Run specific test module
pytest tests/test_article_extractor.py -v

# Run specific test class or function
pytest tests/test_routes.py::TestRoutes::test_home_api_request -v

# Run tests with specific markers
pytest -m "not slow"  # Skip slow tests
pytest -m unit        # Run only unit tests

# Test supported sites configuration
python test_sites.py

# Robust site testing with error handling
python test_sites_robust.py

# Test authentication endpoints
python test_auth_system.py

# Setup test environment
python setup_test_env.py
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
All AI prompts are centralized in `prompts.py`:
- `GROK_CONTEXT_JARGON_PROMPT_SCHEMA`: Term explanations with JSON schema
- `GROK_ALTERNATIVE_VIEWPOINTS_PROMPT`: Multi-source perspective analysis
- `GROK_FACT_CHECK_PROMPT`: Claim verification with credibility scoring
- `GROK_BIAS_ANALYSIS_PROMPT`: Political lean and tone analysis
- `GROK_TIMELINE_PROMPT`: Event chronology with context
- `GROK_EXPERT_OPINIONS_PROMPT`: Expert quote collection with source validation

### Chrome Extension Structure
- **manifest.json**: Configured for 50+ Greek news sites with Supabase permissions
- **content_script_clean.js**: Complete UI implementation with sidebar and reader mode
- **background.js**: Service worker for API communication and message handling
- **popup-auth.html/js**: Main authentication UI with magic link support
- **popup-supabase.html/js**: Alternative Supabase authentication UI
- **js/supabase-auth.js**: Supabase client configuration
- **css/content_styles.css**: Extension styling for sidebar and reader mode

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

## Memories
- Run these tests after changes
```