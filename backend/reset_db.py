"""
Reset database - USE WITH CAUTION
This will drop and recreate all tables
"""
import os
import sys
import psycopg
from django.conf import settings

# Setup Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

import django
django.setup()

def reset_database():
    """Drop and recreate all tables"""
    
    db_settings = settings.DATABASES['default']
    
    # Connect to PostgreSQL
    conn_params = {
        'host': db_settings['HOST'],
        'port': db_settings['PORT'],
        'user': db_settings['USER'],
        'password': db_settings['PASSWORD'],
        'dbname': 'postgres'  # Connect to default db first
    }
    
    db_name = db_settings['NAME']
    
    print(f"WARNING: This will delete database '{db_name}' and all its data!")
    response = input("Are you sure? Type 'yes' to continue: ")
    
    if response.lower() != 'yes':
        print("Cancelled.")
        return
    
    try:
        # Connect to PostgreSQL
        with psycopg.connect(**conn_params) as conn:
            conn.autocommit = True
            with conn.cursor() as cur:
                # Terminate existing connections
                print(f"Terminating connections to {db_name}...")
                cur.execute(f"""
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = '{db_name}' AND pid <> pg_backend_pid()
                """)
                
                # Drop database
                print(f"Dropping database {db_name}...")
                cur.execute(f'DROP DATABASE IF EXISTS "{db_name}"')
                
                # Create database
                print(f"Creating database {db_name}...")
                cur.execute(f'CREATE DATABASE "{db_name}"')
                
        print("Database reset complete!")
        print("\nNow run: python fix_migrations.py")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    reset_database()