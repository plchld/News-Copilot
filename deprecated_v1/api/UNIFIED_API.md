# Unified Analysis API v2.0

**Last Updated:** 2025-05-27  
**Status:** ✅ Production Ready  
**Caching:** Disabled for simplicity

News Copilot uses a single, clean API endpoint for all article analyses with comprehensive error handling and validation.

## 🚀 Main Endpoint

```
POST /api/analyze
```

### Request Format

```json
{
  "url": "https://example.com/article",
  "types": ["jargon", "viewpoints", "fact-check", "bias", "timeline", "expert", "x-pulse"]
}
```

### Response Format

```json
{
  "results": {
    "jargon": { "markdown_content": "..." },
    "viewpoints": { "markdown_content": "..." },
    "fact-check": { "markdown_content": "..." },
    "bias": { /* structured data */ },
    "timeline": { /* structured data */ },
    "expert": { /* structured data */ },
    "x-pulse": { /* structured data */ }
  },
  "errors": {
    "timeline": "Analysis timed out"
  },
  "metadata": {
    "total_time_seconds": 4.2,
    "analyses_requested": 7,
    "analyses_completed": 6,
    "analyses_failed": 1,
    "user_tier": "free",
    "api_version": "2.0.0",
    "execution_details": { /* internal metrics */ }
  }
}
```

## ✨ Key Features

- **🎯 Single endpoint** for all analysis types
- **⚡ Parallel execution** - all analyses run concurrently  
- **🔄 Partial success** - get results even if some analyses fail
- **🔐 Authentication aware** - free tier gets basic analyses, premium gets all
- **🛡️ Comprehensive validation** - request validation and error handling
- **📊 Performance monitoring** - detailed metrics and logging
- **🚫 No caching complexity** - simplified architecture

## 📋 Available Analysis Types

### 🆓 Free Tier (No authentication required)
- `jargon` - Term explanations and definitions
- `viewpoints` - Alternative perspectives and stakeholder views
- `fact-check` - Fact verification and claim checking
- `bias` - Political bias and framing analysis

### 💎 Premium Tier (Authentication required)
- `timeline` - Event chronology and historical context
- `expert` - Expert opinions and professional analysis  
- `x-pulse` - Social media discourse analysis

### 📂 Categories
- **Basic**: `jargon`, `viewpoints`
- **Verification**: `fact-check`, `bias`
- **Premium**: `timeline`, `expert`, `x-pulse`

## 🔧 Additional Endpoints

### Get Analysis Types
```
GET /api/analyze/types
```
Returns available analysis types, categories, and limits.

### Health Check
```
GET /api/analyze/health
```
Returns API health status and configuration.

### Statistics (Admin Only)
```
GET /api/analyze/stats
```
Returns API statistics and configuration details.

## ⚠️ Request Validation

The API validates:
- ✅ URL format (must start with http:// or https://)
- ✅ Analysis types (must be valid and no duplicates)
- ✅ Request limits (max 7 analysis types per request)
- ✅ Authentication for premium features
- ✅ JSON format and required fields

## 📊 Response Status Codes

- **200** - Full success (all analyses completed)
- **207** - Partial success (some analyses failed)
- **400** - Bad request (validation failed)
- **401** - Authentication required for premium features
- **500** - Server error (no analyses completed)
- **503** - Service unhealthy

## 🔄 Migration from Legacy Endpoints

### ❌ Deprecated Endpoints (REMOVED)
- `/api/analysis/stream` → Use `/api/analyze` with `types: ["jargon", "viewpoints"]`
- `/api/analysis/deep` → Use `/api/analyze` with single type in array
- `/api/analysis/selective` → Use `/api/analyze` directly

### ✅ New Unified Approach

```typescript
// Old way (DEPRECATED)
import { startSelectiveAnalysis, fetchDeepAnalysis } from '@/lib/api'

// New way (RECOMMENDED)
import { analyzeArticle } from '@/lib/api-unified'

// Example usage
const response = await fetch('/api/analyze', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    url: 'https://example.com/article',
    types: ['jargon', 'viewpoints', 'fact-check']
  })
});

const data = await response.json();

// Handle results
Object.entries(data.results).forEach(([type, result]) => {
  console.log(`${type} analysis:`, result);
});

// Handle errors
Object.entries(data.errors).forEach(([type, error]) => {
  console.error(`${type} failed:`, error);
});
```

## 🎯 Best Practices

1. **Request only needed analyses** - Don't request all types if you only need specific ones
2. **Handle partial failures** - Check both `results` and `errors` in response
3. **Respect rate limits** - Free tier has lower limits than premium
4. **Use appropriate timeouts** - Analysis can take 30-60 seconds
5. **Check status codes** - 207 means partial success, not failure

## 🔍 Example Requests

### Basic Analysis (Free)
```bash
curl -X POST http://localhost:8080/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/article", "types": ["jargon", "viewpoints"]}'
```

### Fact Check Only
```bash
curl -X POST http://localhost:8080/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/article", "types": ["fact-check"]}'
```

### Multiple Free Analyses
```bash
curl -X POST http://localhost:8080/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/article", "types": ["jargon", "viewpoints", "fact-check", "bias"]}'
```

## 🏗️ Architecture Improvements

### ✅ What's New in v2.0
- **Removed caching complexity** - Simplified architecture
- **Enhanced validation** - Comprehensive request validation
- **Better error handling** - Detailed error messages and status codes
- **Performance monitoring** - Request metrics and logging
- **Cleaned up legacy code** - Removed deprecated endpoints
- **Improved documentation** - Clear examples and best practices

### 🗑️ What Was Removed
- Legacy endpoints (`/api/analysis/*`)
- Complex caching system
- Deprecated test files
- Unused route handlers
- FastAPI duplicate endpoints

## 🚀 Performance

- **No caching overhead** - Direct execution for all requests
- **Parallel processing** - Multiple analyses run concurrently
- **Optimized agents** - Streamlined analysis pipeline
- **Better error recovery** - Partial results on failure
- **Comprehensive logging** - Performance monitoring and debugging