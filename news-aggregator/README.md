# News Aggregator v2 - Greek News with Comprehensive AI Analysis

A sophisticated news aggregation system that extracts articles from Greek news sites and enriches them with comprehensive AI-powered analysis using multiple specialized agents.

## 🚀 Features

### Article Processing
- **JavaScript Support**: Selenium-based extraction for dynamic sites like AMNA
- **Fallback Extraction**: Trafilatura for traditional sites
- **Structured Storage**: Article indexing with metadata and search capabilities
- **Multiple Formats**: JSON, TXT, Markdown exports

### AI Analysis (6 Specialized Agents)
- **🔤 Jargon Agent**: Technical term explanations
- **👁️ Viewpoints Agent**: Alternative perspectives and opinions
- **✅ Fact-Check Agent**: Claim verification and source checking
- **⚖️ Bias Agent**: Political bias analysis on Greek political spectrum
- **📅 Timeline Agent**: Event chronology and temporal analysis
- **🎓 Expert Agent**: Expert opinion collection and analysis

### Advanced Capabilities
- **Parallel Processing**: All agents run concurrently for 3x faster analysis
- **Dynamic Model Selection**: Optimized model choice based on task complexity
- **Quality Control**: Multi-pass refinement and error handling
- **Cost Optimization**: Strategic use of grok-3 vs grok-3-mini

## 🏃 Quick Start

1. **Environment Setup**
   ```bash
   cp .env.example .env
   # Edit .env and add your XAI_API_KEY
   
   pip install -r requirements.txt
   ```

2. **Test Core System**
   ```bash
   # Test article extraction
   python test_amna_article.py
   
   # Test comprehensive AI enrichment
   python test_comprehensive_system.py
   ```

3. **Launch Web Interface**
   ```bash
   python web_app.py
   # Open http://localhost:5001
   ```

## 📁 Architecture

```
news-aggregator/
├── agents/                    # AI Agent System
│   ├── news_agent_coordinator.py    # Orchestrates all agents
│   ├── jargon_agent.py              # Term explanations
│   ├── viewpoints_agent.py          # Alternative perspectives  
│   ├── fact_check_agent.py          # Fact verification
│   ├── bias_agent.py                # Political bias analysis
│   ├── timeline_agent.py            # Event chronology
│   ├── expert_agent.py              # Expert opinions
│   └── schemas.py                   # Structured response schemas
├── processors/               # Processing Pipeline
│   ├── article_processor.py         # Core extraction
│   ├── enhanced_extractor.py        # Selenium support
│   ├── simple_ai_enrichment.py      # Basic AI enrichment
│   ├── comprehensive_ai_enrichment.py # Full agent system
│   └── enhanced_article_processor.py  # Complete pipeline
├── storage/                  # Data Management
│   └── article_storage.py           # Article indexing & retrieval
├── config/                   # Configuration
│   └── config.py                    # Settings and API configs
├── templates/                # Web Interface
│   └── index.html                   # Modern responsive UI
└── data/                     # Storage Directories
    ├── processed/            # Original articles with metadata
    ├── enriched/             # AI-enriched articles
    └── exports/              # Export formats
```

## 🌐 Web Interface

- **Article Processing**: Paste URL for instant analysis
- **Article Library**: Browse and search processed articles  
- **Rich Display**: View original content + all AI enrichments
- **Real-time Updates**: Live processing status and progress
- **Responsive Design**: Works on desktop and mobile

## 🔧 API Endpoints

### Core Endpoints
- `GET /` - Web interface
- `POST /process` - Process article URL
- `GET /articles` - List stored articles
- `GET /article/<id>` - Get specific article with enrichments
- `GET /health` - System health check

### Query Parameters
- `/articles?enriched_only=true` - Only enriched articles
- `/articles?limit=50` - Limit results

## ⚙️ Configuration

### AI Models (`config/config.py`)
```python
AGENT_CONFIG = {
    "jargon": {"model": "grok-3-mini", "timeout": 30},
    "viewpoints": {"model": "grok-3", "timeout": 60},
    "fact_check": {"model": "grok-3", "timeout": 60},
    # ... optimized per agent
}
```

### Storage Directories
```python
EXPORT_DIR = "data/exports"      # Raw exports
PROCESSED_DIR = "data/processed"  # Processed articles
ENRICHED_DIR = "data/enriched"   # AI-enriched articles
```

## 🎯 Supported Sites

### Primary Support
- **AMNA (amna.gr)**: Full JavaScript rendering support
- **Extensible**: Framework supports any Greek news site

### Technical Support
- **Static Sites**: Trafilatura extraction
- **Dynamic Sites**: Selenium with Chrome/Chromium
- **Fallback Chains**: Multiple extraction strategies

## 🧪 Testing

```bash
# Test individual components
python test_basic_setup.py          # Import validation
python test_amna_article.py         # Article extraction
python test_simple_enrichment.py    # Basic AI enrichment
python test_comprehensive_system.py # Full system test

# Test specific agents
python -c "from agents.jargon_agent import JargonAgent; print('Jargon agent OK')"
```

## 📊 Performance

### Processing Speed
- **Extraction**: 5-15 seconds (depends on site complexity)
- **AI Analysis**: 30-120 seconds (6 agents in parallel)
- **Storage**: Near-instant with indexing

### Cost Optimization
- **grok-3-mini**: Simple tasks (jargon, summaries)
- **grok-3**: Complex analysis (bias, fact-checking, viewpoints)
- **Parallel Execution**: Reduces total processing time by ~70%

## 🔮 Migration from v1

If migrating from the original system:

```bash
# Run migration script
python migrate_old_system.py

# Test new system
python test_comprehensive_system.py

# Start using new interface
python web_app.py
```

## 🛣️ Roadmap

### Immediate (v2.1)
- [ ] Database integration (PostgreSQL/SQLite)
- [ ] RSS feed monitoring
- [ ] Scheduled article collection
- [ ] User authentication

### Future (v2.x)
- [ ] Multi-source aggregation
- [ ] Advanced search and filtering
- [ ] Export to external systems
- [ ] Real-time notifications
- [ ] Analytics dashboard
- [ ] API rate limiting

## 🤝 Contributing

1. Test the system thoroughly
2. Add new agent types in `agents/`
3. Extend extraction support for new sites
4. Improve web interface features

## 📄 License

This project is part of the News Copilot ecosystem for Greek news analysis.