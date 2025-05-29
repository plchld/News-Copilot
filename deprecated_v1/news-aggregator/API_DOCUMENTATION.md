# News Aggregator API v2 - Documentation

## 🚀 Overview

The News Aggregator API v2 provides comprehensive RESTful endpoints for:
- **Agent Management**: Individual and coordinated AI analysis
- **Article Processing**: Extraction, enrichment, and storage
- **Data Retrieval**: Search, filtering, and export capabilities

## 🏗️ Architecture

```
API Structure:
├── /api/health              # Main API health
├── /api/info               # API information
├── /api/agents/*           # Agent operations
└── /api/articles/*         # Article operations
```

## 🤖 Agent API Endpoints

### Base URL: `/api/agents`

#### Health Check
```http
GET /api/agents/health
```
**Response:**
```json
{
  "status": "healthy",
  "available_agents": ["jargon", "viewpoints", "fact_check", "bias", "timeline", "expert"],
  "api_key_configured": true
}
```

#### List All Agents
```http
GET /api/agents/list
```
**Response:**
```json
{
  "status": "success",
  "agents": {
    "jargon": {
      "name": "jargon",
      "description": "Technical term explanations",
      "config": {"model": "grok-3-mini", "timeout": 30}
    }
  },
  "total_agents": 6
}
```

#### Single Agent Analysis
```http
POST /api/agents/{agent_name}/analyze
```
**Available agents:** `jargon`, `viewpoints`, `fact_check`, `bias`, `timeline`, `expert`

**Request Body:**
```json
{
  "content": "Article content to analyze",
  "url": "https://example.com/article",
  "config": {}
}
```

**Response:**
```json
{
  "status": "success",
  "agent": "jargon",
  "analysis_status": "success",
  "duration_seconds": 15.3,
  "data": {
    "terms": [
      {
        "term": "Υπουργικό Συμβούλιο",
        "explanation": "Το ανώτατο συλλογικό κυβερνητικό όργανο",
        "context": "Συνεδριάζει για κυβερνητικές αποφάσεις"
      }
    ]
  }
}
```

#### Multiple Agent Analysis
```http
POST /api/agents/analyze-multiple
```
**Request Body:**
```json
{
  "content": "Article content",
  "url": "https://example.com/article",
  "agents": ["jargon", "bias", "viewpoints"],
  "parallel": true
}
```

**Response:**
```json
{
  "status": "success",
  "successful_analyses": ["jargon", "bias"],
  "failed_analyses": ["viewpoints"],
  "total_duration_seconds": 45.2,
  "results": {
    "jargon": {
      "status": "success",
      "data": {...}
    },
    "bias": {
      "status": "success", 
      "data": {...}
    }
  }
}
```

#### Full Analysis (All Agents)
```http
POST /api/agents/analyze-full
```
**Request Body:**
```json
{
  "content": "Article content",
  "url": "https://example.com/article"
}
```

#### Batch Analysis
```http
POST /api/agents/batch
```
**Request Body:**
```json
{
  "tasks": [
    {
      "id": "task1",
      "content": "Content 1",
      "url": "URL 1", 
      "agents": ["jargon", "bias"]
    },
    {
      "id": "task2",
      "content": "Content 2",
      "agents": ["viewpoints"]
    }
  ]
}
```

#### Agent Configuration
```http
GET /api/agents/{agent_name}/config
```

## 📄 Article API Endpoints

### Base URL: `/api/articles`

#### Health Check
```http
GET /api/articles/health
```

#### Process New Article
```http
POST /api/articles/process
```
**Request Body:**
```json
{
  "url": "https://www.amna.gr/home/article/123456/...",
  "enrich": true,
  "analyses": ["jargon", "bias"]
}
```

**Response:**
```json
{
  "status": "success",
  "article_id": "abc123def456",
  "title": "Article Title",
  "enriched": true,
  "enrichment_type": "comprehensive",
  "analyses_completed": ["jargon", "bias", "viewpoints"],
  "enrichment_duration": 67.8
}
```

#### List Articles
```http
GET /api/articles/list?limit=20&enriched_only=true&source=www.amna.gr
```
**Query Parameters:**
- `limit`: Maximum articles (default: 20)
- `enriched_only`: Show only enriched articles (default: false)
- `source`: Filter by source domain
- `search`: Search in title/content

**Response:**
```json
{
  "status": "success",
  "articles": [
    {
      "id": "abc123",
      "title": "Article Title",
      "url": "https://...",
      "source_domain": "www.amna.gr",
      "word_count": 456,
      "enriched": true,
      "storage_date": "2025-05-28T12:00:00"
    }
  ],
  "total_found": 15,
  "storage_stats": {...}
}
```

#### Get Specific Article
```http
GET /api/articles/{article_id}
```

#### Get Article Enrichments
```http
GET /api/articles/{article_id}/enrichments
```

#### Get Specific Enrichment
```http
GET /api/articles/{article_id}/enrichments/{analysis_type}
```
**Available types:** `jargon`, `viewpoints`, `fact_check`, `bias`, `timeline`, `expert`

#### Export Article
```http
GET /api/articles/{article_id}/export?format=json&include_enrichments=true
```
**Query Parameters:**
- `format`: `json`, `txt`, `md` (default: json)
- `include_enrichments`: `true`/`false` (default: true)

#### Search Articles
```http
POST /api/articles/search
```
**Request Body:**
```json
{
  "query": "search terms",
  "filters": {
    "source_domain": "www.amna.gr",
    "enriched_only": true,
    "date_from": "2025-01-01",
    "date_to": "2025-12-31"
  },
  "limit": 50
}
```

#### Article Statistics
```http
GET /api/articles/stats
```

## 🔧 Usage Examples

### Python Client Example
```python
import requests

BASE_URL = "http://localhost:5001"

# Process article with specific analyses
response = requests.post(f"{BASE_URL}/api/articles/process", json={
    "url": "https://www.amna.gr/home/article/123456/...",
    "enrich": True,
    "analyses": ["jargon", "bias"]
})

if response.status_code == 200:
    data = response.json()
    article_id = data['article_id']
    
    # Get enrichments
    enrichments = requests.get(f"{BASE_URL}/api/articles/{article_id}/enrichments")
    print(enrichments.json())
```

### JavaScript/Fetch Example
```javascript
// Analyze content with specific agent
const response = await fetch('/api/agents/jargon/analyze', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        content: 'Το Υπουργικό Συμβούλιο συνεδριάζει...',
        url: 'https://example.com'
    })
});

const result = await response.json();
console.log(result.data);
```

### cURL Examples
```bash
# List available agents
curl -X GET http://localhost:5001/api/agents/list

# Analyze with jargon agent
curl -X POST http://localhost:5001/api/agents/jargon/analyze \
  -H "Content-Type: application/json" \
  -d '{"content": "Text to analyze", "url": "https://example.com"}'

# Process article
curl -X POST http://localhost:5001/api/articles/process \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.amna.gr/home/article/123456/..."}'
```

## 🚦 Response Codes

- **200**: Success
- **400**: Bad request (missing parameters, invalid data)
- **404**: Resource not found (article, agent, endpoint)
- **500**: Internal server error

## 🔐 Authentication

Currently, the API uses the `XAI_API_KEY` environment variable for Grok API access. Future versions will include:
- User authentication
- API key management
- Rate limiting

## 📊 Performance

### Typical Response Times
- **Agent Analysis**: 15-60 seconds (depends on agent and content length)
- **Article Processing**: 30-120 seconds (extraction + enrichment)
- **Data Retrieval**: <1 second (from storage)
- **Parallel Analysis**: ~70% faster than sequential

### Optimization Tips
- Use `parallel: true` for multiple agent analysis
- Specify only needed `analyses` to reduce processing time
- Use `enriched_only=true` for faster article listing

## 🛠️ Development

### Running the API
```bash
cd news-aggregator
python web_app.py
# API available at http://localhost:5001/api/*
```

### Testing
```bash
# Test API endpoints
python test_api_system.py

# Test individual components
python test_core_system.py
```

### Adding New Agents
1. Create agent class in `agents/`
2. Add to `NewsAgentCoordinator`
3. Update `individual_agents` in `agent_api.py`
4. Test with `/api/agents/list`

---

**News Aggregator API v2** - Comprehensive Greek news analysis with AI agents