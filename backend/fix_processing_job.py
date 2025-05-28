#!/usr/bin/env python3
"""
Fix ProcessingJob model - make article field nullable
Run this script to create the migration manually
"""

MIGRATION_CONTENT = '''# Generated migration for ProcessingJob article nullable field

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('news_aggregator', '0002_auto_20250528_1901'),  # Update with actual latest migration
    ]

    operations = [
        migrations.AlterField(
            model_name='processingjob',
            name='article',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='jobs', to='news_aggregator.article'),
        ),
    ]
'''

def create_migration():
    import os
    
    # Find the migrations directory
    migrations_dir = '/mnt/c/Repositories/News-Copilot/backend/apps/news_aggregator/migrations'
    
    if not os.path.exists(migrations_dir):
        print(f"Creating migrations directory: {migrations_dir}")
        os.makedirs(migrations_dir, exist_ok=True)
    
    # Find the latest migration number
    existing_migrations = [f for f in os.listdir(migrations_dir) if f.startswith('00') and f.endswith('.py')]
    if existing_migrations:
        # Extract numbers and find the highest
        numbers = []
        for f in existing_migrations:
            try:
                num = int(f.split('_')[0])
                numbers.append(num)
            except ValueError:
                continue
        
        if numbers:
            next_num = max(numbers) + 1
        else:
            next_num = 3
    else:
        next_num = 1
    
    # Create the migration file
    migration_filename = f"{next_num:04d}_processing_job_nullable_article.py"
    migration_path = os.path.join(migrations_dir, migration_filename)
    
    # Update the dependency in the migration content
    if existing_migrations:
        latest_migration = max(existing_migrations, key=lambda x: int(x.split('_')[0]))
        latest_migration_name = latest_migration.replace('.py', '')
        updated_content = MIGRATION_CONTENT.replace(
            "('news_aggregator', '0002_auto_20250528_1901')",
            f"('news_aggregator', '{latest_migration_name}')"
        )
    else:
        updated_content = MIGRATION_CONTENT.replace(
            "('news_aggregator', '0002_auto_20250528_1901')",
            "('news_aggregator', '__first__')"
        )
    
    with open(migration_path, 'w') as f:
        f.write(updated_content)
    
    print(f"Created migration: {migration_path}")
    print("Now run: python manage.py migrate news_aggregator")

if __name__ == "__main__":
    create_migration()