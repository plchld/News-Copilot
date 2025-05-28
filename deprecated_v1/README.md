# Deprecated News Copilot System (v1)

This folder contains the original News Copilot system that was migrated on migrate_old_system.py.

## What's Here

- **api/**: Original Flask API with agent system
- **web/**: Next.js web interface  
- **static/**: Static HTML files
- **tests/**: Test suites
- **debug/**: Debugging tools
- **docs/**: Documentation
- **extension/**: Chrome extension (deprecated)

## Migration to v2

The new system is located in `news-aggregator/` and includes:

- Enhanced article extraction with Selenium support
- Comprehensive AI enrichment system
- Structured storage with indexing
- Improved web interface
- Better error handling and logging

## Using This Deprecated System

If needed, you can still run the old system:

```bash
cd deprecated_v1
python api/index.py  # Start old API
cd web && npm run dev  # Start old web interface
```

⚠️ **Note**: This system is no longer maintained. Use `news-aggregator/` for new development.
