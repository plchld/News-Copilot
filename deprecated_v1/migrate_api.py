#!/usr/bin/env python3
"""Script to migrate API to new web-focused structure"""

import os
import shutil
import sys

def backup_file(src):
    """Create backup of file before moving"""
    if os.path.exists(src):
        backup = f"{src}.backup"
        shutil.copy2(src, backup)
        print(f"✓ Backed up {src}")

def safe_move(src, dst):
    """Safely move file with backup"""
    if os.path.exists(src):
        backup_file(src)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.move(src, dst)
        print(f"✓ Moved {src} -> {dst}")
    else:
        print(f"⚠ Source not found: {src}")

def main():
    """Execute API migration"""
    
    print("Starting API migration to web-focused structure...\n")
    
    # 1. Move test files out of API directory
    test_files = [
        'api/test_concurrent_execution.py',
        'api/test_enhanced_logging.py',
        'api/enhanced_analysis_example.py'
    ]
    
    for test_file in test_files:
        if os.path.exists(test_file):
            safe_move(test_file, test_file.replace('api/', 'deprecated/'))
    
    # 2. Clean up duplicate auth files
    print("\nCleaning up authentication files...")
    
    # Backup all auth files first
    auth_files = [
        'api/auth.py',
        'api/simple_auth.py', 
        'api/supabase_auth.py',
        'api/http_supabase.py',
        'api/auth_routes.py'
    ]
    
    for auth_file in auth_files:
        if os.path.exists(auth_file):
            backup_file(auth_file)
    
    # Move to deprecated
    for auth_file in auth_files:
        if os.path.exists(auth_file):
            safe_move(auth_file, auth_file.replace('api/', 'deprecated/'))
    
    # 3. Update imports in moved files
    print("\nUpdating imports in core files...")
    
    core_files = [
        'api/core/analysis_handlers.py',
        'api/core/article_extractor.py',
        'api/core/grok_client.py'
    ]
    
    for file_path in core_files:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Update imports to use absolute imports within api directory
            content = content.replace('from prompt_utils', 'from utils.prompt_utils')
            content = content.replace('from search_params_builder', 'from utils.search_params_builder')
            content = content.replace('from thinking_utils', 'from utils.thinking_utils')
            content = content.replace('from config import', 'from config import')
            content = content.replace('import config', 'from config import config')
            
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"✓ Updated imports in {file_path}")
    
    # 4. Update agent imports
    print("\nUpdating agent imports...")
    
    agent_files = [f for f in os.listdir('api/agents') if f.endswith('.py') and f != '__init__.py']
    
    for agent_file in agent_files:
        file_path = f'api/agents/{agent_file}'
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Update imports
            content = content.replace('from prompt_utils', 'from ..utils.prompt_utils')
            content = content.replace('from search_params_builder', 'from ..utils.search_params_builder')
            content = content.replace('from grok_client', 'from ..core.grok_client')
            content = content.replace('from config import', 'from ..config import')
            
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"✓ Updated imports in {file_path}")
    
    # 5. Replace old files with new ones
    print("\nReplacing with new implementations...")
    
    if os.path.exists('api/app_new.py'):
        backup_file('api/app.py')
        shutil.move('api/app_new.py', 'api/app.py')
        print("✓ Replaced app.py with new version")
    
    if os.path.exists('api/config_new.py'):
        backup_file('api/config.py')
        shutil.move('api/config_new.py', 'api/config.py')
        print("✓ Replaced config.py with new version")
    
    # 6. Clean up obsolete files
    print("\nMoving obsolete files...")
    
    obsolete_files = [
        'api/routes.py',
        'api/web_routes.py',
        'api/optimized_endpoints.py',
        'api/admin_auth.py'
    ]
    
    for obsolete_file in obsolete_files:
        if os.path.exists(obsolete_file):
            safe_move(obsolete_file, obsolete_file.replace('api/', 'deprecated/'))
    
    print("\n✅ Migration completed successfully!")
    print("\nNext steps:")
    print("1. Review the changes and test the API")
    print("2. Update vercel.json if needed")
    print("3. Install the Next.js web app: cd web && npm install")
    print("4. Start the development servers:")
    print("   - API: python api/index.py")
    print("   - Web: cd web && npm run dev")

if __name__ == '__main__':
    main()