"""
Test script to verify the Django setup is working
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

def test_imports():
    """Test that all our modules can be imported"""
    print("Testing imports...")
    
    try:
        from apps.news_aggregator.models import Article, NewsSource
        print("✓ Models imported successfully")
    except Exception as e:
        print(f"✗ Model import failed: {e}")
        return False
    
    try:
        from apps.news_aggregator.extractors.article import ArticleExtractor
        print("✓ Article extractor imported successfully")
    except Exception as e:
        print(f"✗ Extractor import failed: {e}")
        return False
    
    try:
        from apps.news_aggregator.agents.base import BaseAgent
        print("✓ Base agent imported successfully")
    except Exception as e:
        print(f"✗ Agent import failed: {e}")
        return False
    
    try:
        from apps.news_aggregator.grok_client import get_grok_client
        print("✓ Grok client imported successfully")
    except Exception as e:
        print(f"✗ Grok client import failed: {e}")
        return False
    
    return True

def test_database():
    """Test database connection"""
    print("\nTesting database connection...")
    
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print("✓ Database connection successful")
        return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False

def test_extractor():
    """Test article extractor with a simple HTML string"""
    print("\nTesting article extractor...")
    
    try:
        from apps.news_aggregator.extractors.article import ArticleExtractor
        extractor = ArticleExtractor()
        
        # Test with simple HTML parsing (not actual web fetch)
        html = """
        <html>
        <head><title>Test Article</title></head>
        <body>
        <h1>Test Title</h1>
        <p>This is a test paragraph.</p>
        <p>Another paragraph with content.</p>
        </body>
        </html>
        """
        
        result = extractor._extract_with_beautifulsoup(html, "http://test.com")
        if result and result.get('title'):
            print("✓ Article extractor working")
            return True
        else:
            print("✗ Article extractor not returning expected results")
            return False
            
    except Exception as e:
        print(f"✗ Article extractor test failed: {e}")
        return False

def main():
    print("=== News Copilot Setup Test ===\n")
    
    success = True
    
    success &= test_imports()
    success &= test_database()
    success &= test_extractor()
    
    print(f"\n=== Test Results ===")
    if success:
        print("✓ All tests passed! Setup is working correctly.")
        print("\nYou can now try:")
        print("python manage.py test_extraction https://www.amna.gr/home/article/907263/Chrimatistirio-Se-nea-upsila-15-eton-i-agora-me-othisi-apo-to-deal-tis-Alpha-Unicredit")
    else:
        print("✗ Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == '__main__':
    main()