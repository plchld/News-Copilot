"""
Script to fix migration dependencies
Run this instead of manage.py migrate for initial setup
"""
import os
import sys
import django
from django.core.management import execute_from_command_line

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

def run_command(cmd, *args):
    """Run a Django management command"""
    print(f"\n>>> Running: {cmd} {' '.join(args)}")
    try:
        execute_from_command_line(['manage.py', cmd] + list(args))
        print("✓ Success")
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    return True

def main():
    print("=== Fixing Django Migrations ===\n")
    
    # Step 1: Create migrations for core app first (has User model)
    print("Step 1: Creating core app migrations...")
    if not run_command('makemigrations', 'core'):
        print("Failed to create core migrations")
        return
    
    # Step 2: Create migrations for other apps
    print("\nStep 2: Creating other app migrations...")
    for app in ['authentication', 'news_aggregator', 'api']:
        run_command('makemigrations', app)
    
    # Step 3: Run migrations in specific order
    print("\nStep 3: Running migrations in correct order...")
    
    # First, create the database tables for Django's built-in apps
    # but NOT admin yet (it depends on User)
    for app in ['contenttypes', 'auth', 'sessions']:
        run_command('migrate', app)
    
    # Now migrate core (creates User table)
    run_command('migrate', 'core')
    
    # Now we can migrate admin (depends on User)
    run_command('migrate', 'admin')
    
    # Finally, run all remaining migrations
    run_command('migrate')
    
    print("\n=== Migration setup complete! ===")
    print("\nYou can now run: python manage.py createsuperuser")

if __name__ == '__main__':
    main()