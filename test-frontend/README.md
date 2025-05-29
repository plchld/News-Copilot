# News Copilot - Agent Testing Frontend

A simple, lightweight testing interface for quickly testing your AI agents with AMNA.gr articles.

## 🚀 Quick Start (Recommended - Direct Testing)

The easiest way to test your agents is using the Django management command directly, which bypasses authentication:

### 1. Start Django Backend
```bash
cd backend
python manage.py runserver 8000
```

### 2. Test Agents Directly (No UI needed)
```bash
cd backend

# Test with enhanced extraction only
python manage.py process_article "https://www.amna.gr/home/article/YOUR_URL" --enhanced

# Test with full AI analysis (all agents)
python manage.py process_article "https://www.amna.gr/home/article/YOUR_URL" --enhanced --analyze
```

This will show detailed logs and results directly in your terminal, testing all 4 AI agents.

## 🌐 Web Interface Setup

The test frontend automatically detects your backend authentication configuration!

### Option 1: Disable Authentication (Easiest)

```bash
# Set AUTH_REQUIRED=false in your environment
export AUTH_REQUIRED=false

# Or add it to your .env file
echo "AUTH_REQUIRED=false" >> backend/.env

# Start the backend
cd backend
python manage.py runserver 8000

# Start test frontend
cd test-frontend
python server.py 3001
```

Open http://localhost:3001 - the interface will show "🎯 Testing Mode Active" and work without authentication!

### Option 2: Keep Authentication Enabled

If you want to keep `AUTH_REQUIRED=true`, you'll need to set up authentication (see the web interface for instructions), but we recommend using the direct command instead.

## Features

- 🔍 **Auto-detection**: Automatically detects your `AUTH_REQUIRED` setting
- 🚀 **One-click processing**: Uses enhanced Selenium extraction for AMNA.gr
- 🤖 **All agents tested**: Tests all 4 AI agents (Jargon, Viewpoints, Fact Check, Timeline)
- 📊 **Real-time progress**: Shows extraction and analysis progress with detailed logging
- 🎯 **Two testing modes**: Direct command (always works) or web interface (when AUTH_REQUIRED=false)
- 📱 **Clean interface**: Simple, functional design optimized for testing

## Supported AI Agents

The testing interface validates all 4 specialized agents:

- 📚 **Jargon Analysis**: Technical term explanations (grok-3-mini)
- 🔄 **Viewpoints Analysis**: Alternative perspectives with live search (grok-3)
- ✅ **Fact Check Analysis**: Claim verification with search (grok-3)
- 📅 **Timeline Analysis**: Event chronology (grok-3)

## Example Workflow

### Direct Command (Always works):
```bash
python manage.py process_article "https://www.amna.gr/home/article/xxxxx" --enhanced --analyze
```

**Output**:
- Real-time extraction progress with Selenium WebDriver
- Individual agent execution logs and timing
- Structured JSON results for each analysis type
- Database storage of article and analysis results

### Web Interface (When AUTH_REQUIRED=false):
1. **Input**: Enter AMNA.gr URL in browser interface
2. **Processing**: Enhanced Selenium extraction + AI analysis via API
3. **Output**: Article metadata + all 4 agent results in structured format

## Configuration

### Environment Requirements
Make sure your backend has:
```bash
# Required environment variables
XAI_API_KEY=your-grok-api-key
DATABASE_URL=your-database-url

# Optional: Disable authentication for testing
AUTH_REQUIRED=false

# Optional: Supabase (if using Supabase auth)
SUPABASE_URL=your-supabase-url
```

### Backend Status Check
The test frontend automatically checks your backend configuration:

- **🎯 Testing Mode Active**: `AUTH_REQUIRED=false` - Web interface works directly
- **🔐 Authentication Required**: `AUTH_REQUIRED=true` - Use direct command recommended
- **❌ Backend Connection Failed**: Backend not running or wrong URL

### Backend API Endpoints
The system uses these Django endpoints:
- `GET /api/v1/health/` - Check auth requirements and backend status
- `GET /api/testing-info/` - Available when AUTH_REQUIRED=false
- `POST /api/v1/process/` - Process article with enhanced extraction
- `POST /api/v1/analyze/` - Run AI analysis on article  
- `GET /api/v1/articles/{id}/` - Get article details
- `GET /api/v1/articles/{id}/analyses/` - Get analysis results

## Troubleshooting

### Backend Connection Issues
**Problem**: "Backend Connection Failed"
**Solution**: 
- Verify Django is running: `python manage.py runserver 8000`
- Check the API URL in the interface matches your backend
- Look at Django logs for errors

### Authentication Issues
**Problem**: Web interface shows "Authentication Required"
**Solution**: 
- **Recommended**: Use direct command: `python manage.py process_article "URL" --enhanced --analyze`
- **Alternative**: Set `AUTH_REQUIRED=false` in your environment

### AMNA.gr Extraction Issues
**Problem**: "Failed to extract article content"
**Solution**: 
- Ensure Chrome/Chromium is installed
- AMNA.gr requires JavaScript processing (enhanced extractor)
- Check that the AMNA URL is accessible and valid

### Agent Analysis Issues
**Problem**: Analysis fails or returns empty results
**Solution**:
- Verify `XAI_API_KEY` is set correctly in your environment
- Check Grok API rate limits and quota
- Look at Django logs for detailed error messages

## Performance Testing

The test interface is perfect for:
- ✅ **Agent Response Quality**: See actual Greek analysis results
- ✅ **Processing Speed**: Measure extraction and analysis timing
- ✅ **Error Handling**: Test with various article types and URLs
- ✅ **Configuration Testing**: Validate AUTH_REQUIRED settings

## Development vs Production

### Test Frontend (this tool):
- ✅ **Agent validation**: Test all 4 AI agents
- ✅ **API testing**: Validate endpoints and responses
- ✅ **Performance measurement**: Measure processing times
- ✅ **Configuration testing**: Test different AUTH_REQUIRED settings

### Main Frontend (`frontend/`):
- ✅ **User experience**: Production-ready interface
- ✅ **Authentication flow**: Full Supabase integration
- ✅ **UI/UX polish**: Beautiful, responsive design
- ✅ **Production features**: Complete feature set

## Quick Commands Reference

```bash
# Start backend
cd backend && python manage.py runserver 8000

# Disable auth for web testing
export AUTH_REQUIRED=false

# Test directly (always works)
python manage.py process_article "https://www.amna.gr/article/URL" --enhanced --analyze

# Start test frontend
cd test-frontend && python server.py 3001
```

Use this test frontend for development and validation, then switch to your main frontend for production use. 