# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Architecture

News Copilot is a Greek news intelligence platform with AI-powered contextual analysis. The system consists of:

**Frontend**: Chrome extension (`extension/`) with progressive sidebar UI that provides non-intrusive article analysis
**Backend**: Python Flask server (`explain_with_grok.py`) with Grok AI integration for live search and structured analysis
**Content Processing**: Trafilatura-based article extraction supporting 50+ Greek news sites

The architecture uses Server-Sent Events (SSE) for real-time progress updates and structured JSON schemas for AI responses.

## Development Commands

### Backend Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
echo "XAI_API_KEY=your_key_here" > .env

# Start development server
python explain_with_grok.py --server

# CLI testing mode
python explain_with_grok.py <article_url>

# Test site accessibility
python test_sites.py
```

### Chrome Extension Development
```bash
# Load extension in Chrome
# 1. Open chrome://extensions/
# 2. Enable Developer mode
# 3. Click "Load unpacked" and select extension/ folder

# Test on Greek news sites
# Visit any supported site from manifest.json matches[]
```

### Testing
```bash
# Test supported sites configuration
python test_sites.py

# Robust site testing with error handling
python test_sites_robust.py
```

## Key Technical Details

### API Integration
- **Grok API**: Uses XAI_API_KEY with live search enabled via `search_parameters`
- **Response Formats**: JSON schemas for structured data (jargon, fact-check, bias, timeline, expert opinions)
- **Error Handling**: Comprehensive APIStatusError and connection error handling

### Content Processing
- **Article Extraction**: Trafilatura with fallback mechanisms for complex sites
- **Greek Language**: All prompts and responses in Greek with proper Unicode handling
- **Citation Tracking**: Automatic source verification and URL validation

### Extension Communication
- **SSE Streaming**: Real-time progress updates via `/augment-stream` endpoint
- **Deep Analysis**: POST requests to `/deep-analysis` with analysis_type parameter
- **CORS Setup**: Configured for localhost:8080 communication

### Prompt System
All AI prompts are centralized in `prompts.py`:
- `GROK_CONTEXT_JARGON_PROMPT_SCHEMA`: Term explanations with JSON schema
- `GROK_ALTERNATIVE_VIEWPOINTS_PROMPT`: Multi-source perspective analysis
- `GROK_FACT_CHECK_PROMPT`: Claim verification with credibility scoring
- `GROK_BIAS_ANALYSIS_PROMPT`: Political lean and tone analysis
- `GROK_TIMELINE_PROMPT`: Event chronology with context
- `GROK_EXPERT_OPINIONS_PROMPT`: Expert quote collection with source validation

### Chrome Extension Structure
- **manifest.json**: Configured for 50+ Greek news sites with specific domain matches
- **content_script.js**: Complete UI implementation with sidebar and reader mode
- **background.js**: Service worker for API communication and message handling

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
- `FLASK_PORT`: Optional, defaults to 8080
- `DEBUG_MODE`: Optional development flag

### Extension Permissions
- `activeTab`: Access to current tab content
- `scripting`: Content script injection
- `nativeMessaging`: Future integration capability
- `http://localhost:8080/*`: Backend API communication

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