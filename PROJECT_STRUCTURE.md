# News Copilot v2 - Project Structure

## 🏗️ Clean Architecture

The project has been completely reorganized for v2:

### Root Directory
```
News-Copilot/
├── news-aggregator/          # 🚀 NEW SYSTEM (v2)
├── deprecated_v1/            # 📦 OLD SYSTEM (archived)
├── README.md                 # 📖 Main documentation
├── CLAUDE.md                 # 🤖 Claude instructions
└── *.md                      # 📝 Documentation files
```

### New System (news-aggregator/)
```
news-aggregator/
├── agents/                   # 🤖 AI Agent System
│   ├── news_agent_coordinator.py    # Orchestrates all agents
│   ├── jargon_agent.py              # Term explanations
│   ├── viewpoints_agent.py          # Alternative perspectives
│   ├── fact_check_agent.py          # Fact verification
│   ├── bias_agent.py                # Political bias analysis
│   ├── timeline_agent.py            # Event chronology
│   ├── expert_agent.py              # Expert opinions
│   └── schemas.py                   # Response schemas
├── processors/               # ⚙️ Processing Pipeline
│   ├── article_processor.py         # Core extraction
│   ├── enhanced_extractor.py        # Selenium support
│   ├── simple_ai_enrichment.py      # Basic AI enrichment
│   ├── comprehensive_ai_enrichment.py # Full agent system
│   └── enhanced_article_processor.py  # Complete pipeline
├── storage/                  # 💾 Data Management
│   └── article_storage.py           # Article indexing & retrieval
├── config/                   # ⚙️ Configuration
│   └── config.py                    # Settings and API configs
├── templates/                # 🌐 Web Interface
│   └── index.html                   # Modern responsive UI
├── core/                     # 🔧 Core Services
│   └── grok_client.py               # Grok API client
├── utils/                    # 🛠️ Utilities
│   ├── prompt_utils.py              # Prompt engineering
│   ├── search_params_builder.py     # Search parameter building
│   └── markdown_parser.py           # Markdown response parsing
├── data/                     # 📁 Storage Directories
│   ├── processed/            # Original articles with metadata
│   ├── enriched/             # AI-enriched articles
│   └── exports/              # Export formats
├── web_app.py               # 🌐 Flask web application
├── test_*.py                # 🧪 Test suite
├── requirements.txt         # 📦 Dependencies
└── README.md               # 📖 Documentation
```

### Deprecated System (deprecated_v1/)
```
deprecated_v1/
├── api_original/            # Original Flask API
├── web_original/            # Next.js web interface
├── static_original/         # Static HTML files
├── tests_original/          # Test suites
├── debug_original/          # Debugging tools
├── docs_original/           # Documentation
├── README.md               # Migration information
└── README_original.md      # Backup of original README
```

## 🚀 Key Improvements in v2

### 1. **Modular Architecture**
- Clear separation of concerns
- Independent agent system
- Pluggable processing pipeline

### 2. **Enhanced Processing**
- Selenium support for JavaScript sites
- Multiple extraction fallbacks
- Comprehensive error handling

### 3. **Advanced AI System**
- 6 specialized agents running in parallel
- Dynamic model selection (grok-3 vs grok-3-mini)
- Structured response schemas

### 4. **Robust Storage**
- Article indexing with metadata
- Search and filtering capabilities
- Storage statistics and analytics

### 5. **Modern Web Interface**
- Real-time processing updates
- Rich article display
- Responsive design

## 🎯 Migration Benefits

### Before (v1)
- Monolithic API structure
- Mixed concerns in single files
- Limited error handling
- Basic storage (file-based)

### After (v2)
- Modular, maintainable architecture
- Specialized components
- Comprehensive error handling
- Structured storage with indexing

## 🔄 Usage

### Start New System
```bash
cd news-aggregator
python web_app.py
# Visit http://localhost:5001
```

### Access Old System (if needed)
```bash
cd deprecated_v1
# Old system files available but not maintained
```

## 🛣️ Future Development

All new development should happen in `news-aggregator/`:
- Add new agents in `agents/`
- Extend processors in `processors/`
- Add new storage backends in `storage/`
- Enhance web interface in `templates/`

The deprecated system serves as a reference but should not be modified.

---

*Project restructured on 2025-05-28 for News Copilot v2*