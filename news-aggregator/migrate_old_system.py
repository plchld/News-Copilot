#!/usr/bin/env python3
"""
Migration script to move old system components to deprecated folder
"""
import os
import shutil
from pathlib import Path

def migrate_old_system():
    """Move old system components to deprecated folder"""
    
    # Define source (parent project) and target paths
    parent_dir = Path(__file__).parent.parent
    news_aggregator_dir = Path(__file__).parent
    
    # Create deprecated directory in parent
    deprecated_dir = parent_dir / "deprecated_v1"
    deprecated_dir.mkdir(exist_ok=True)
    
    print("🔄 MIGRATING OLD SYSTEM TO DEPRECATED")
    print("=" * 50)
    
    # Items to move to deprecated
    items_to_move = [
        "api",
        "web", 
        "static",
        "extension",  # If it exists
        "tests",
        "debug",
        "docs",
        "prompts.py",
        "explain_with_grok.py",
        "dev_server.py",
        "migrate_api.py",
        "setup_admin.py",
        "setup_test_env.py",
        "test_*.py",  # Test files in root
        "run_tests.py",
        "vercel.json"
    ]
    
    moved_count = 0
    
    for item in items_to_move:
        source_path = parent_dir / item
        
        # Handle glob patterns
        if "*" in item:
            # Find matching files
            matching_files = list(parent_dir.glob(item))
            for file_path in matching_files:
                target_path = deprecated_dir / file_path.name
                try:
                    if file_path.exists():
                        if file_path.is_file():
                            shutil.copy2(file_path, target_path)
                        else:
                            shutil.copytree(file_path, target_path, dirs_exist_ok=True)
                        print(f"✓ Moved: {file_path.name}")
                        moved_count += 1
                except Exception as e:
                    print(f"✗ Failed to move {file_path.name}: {e}")
        else:
            # Single item
            target_path = deprecated_dir / item
            try:
                if source_path.exists():
                    if source_path.is_file():
                        shutil.copy2(source_path, target_path)
                    else:
                        shutil.copytree(source_path, target_path, dirs_exist_ok=True)
                    print(f"✓ Moved: {item}")
                    moved_count += 1
                else:
                    print(f"⚠ Not found: {item}")
            except Exception as e:
                print(f"✗ Failed to move {item}: {e}")
    
    # Create README in deprecated folder
    readme_content = f"""# Deprecated News Copilot System (v1)

This folder contains the original News Copilot system that was migrated on {os.path.basename(__file__)}.

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
"""
    
    with open(deprecated_dir / "README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    print(f"\n📊 MIGRATION SUMMARY")
    print(f"✓ Moved {moved_count} items to deprecated_v1/")
    print(f"📁 Deprecated folder: {deprecated_dir}")
    print(f"📝 Created README.md with migration info")
    
    # Update main README to point to new system
    main_readme_path = parent_dir / "README.md"
    if main_readme_path.exists():
        print(f"\n📝 Updating main README.md...")
        
        new_readme_content = f"""# News Copilot v2 - Greek News Aggregator

> **Note**: This repository has been upgraded to v2. The old system is in `deprecated_v1/`.

## Quick Start

The new news aggregator system is in `news-aggregator/`:

```bash
cd news-aggregator
pip install -r requirements.txt
cp .env.example .env  # Add your XAI_API_KEY
python web_app.py     # Start web interface
```

Visit http://localhost:5001 to use the new system.

## What's New in v2

- 🚀 **Enhanced Extraction**: Selenium support for JavaScript-heavy sites
- 🤖 **Comprehensive AI**: Full agent system with parallel processing
- 💾 **Structured Storage**: Article indexing and management
- 🎯 **Better UX**: Improved web interface with real-time updates
- 📊 **Analytics**: Storage statistics and processing metrics

## Architecture

- `news-aggregator/` - New system (v2)
- `deprecated_v1/` - Original system (archived)

## Documentation

See `news-aggregator/README.md` for detailed documentation.

---

*Generated by migration script on {os.path.basename(__file__)}*
"""
        
        # Backup existing README
        backup_path = deprecated_dir / "README_original.md"
        shutil.copy2(main_readme_path, backup_path)
        print(f"✓ Backed up original README to deprecated_v1/README_original.md")
        
        # Write new README
        with open(main_readme_path, "w", encoding="utf-8") as f:
            f.write(new_readme_content)
        print(f"✓ Updated main README.md")
    
    print(f"\n🎉 MIGRATION COMPLETED!")
    print(f"")
    print(f"Next steps:")
    print(f"1. Review migrated files in deprecated_v1/")
    print(f"2. Test the new system: cd news-aggregator && python web_app.py")
    print(f"3. Remove old files if everything works: rm -rf deprecated_v1/")

if __name__ == "__main__":
    migrate_old_system()