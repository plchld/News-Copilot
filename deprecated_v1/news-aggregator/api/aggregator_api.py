"""
News Aggregator API
Main API for processing and serving news articles
"""
from flask import Flask, request, jsonify
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from processors.article_processor import ArticleProcessor
from exporters.local_exporter import LocalExporter

app = Flask(__name__)

# Initialize components
processor = ArticleProcessor()
exporter = LocalExporter()


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "news-aggregator"
    })


@app.route('/process-article', methods=['POST'])
def process_article():
    """
    Process a single article from URL
    
    Expected JSON payload:
    {
        "url": "https://example.com/article",
        "export_format": "json"  # optional: json, txt, md
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({"error": "URL is required"}), 400
        
        url = data['url']
        export_format = data.get('export_format', 'json')
        
        print(f"[API] Processing article: {url}")
        
        # Process the article
        article = processor.extract_article(url)
        
        # Export to local file
        export_path = exporter.export_article(article, format=export_format)
        
        # Return processed data
        response = {
            "status": "success",
            "article": {
                "url": article.url,
                "title": article.title,
                "source_domain": article.source_domain,
                "published_date": article.published_date,
                "extracted_date": article.extracted_date,
                "word_count": article.word_count,
                "metadata": article.metadata
            },
            "export_path": export_path,
            "content_preview": article.content[:200] + "..." if len(article.content) > 200 else article.content
        }
        
        return jsonify(response)
        
    except Exception as e:
        print(f"[API] Error processing article: {str(e)}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.route('/process-url', methods=['GET'])
def process_url_get():
    """
    Process a single article from URL via GET parameter
    Usage: /process-url?url=https://example.com/article&format=json
    """
    try:
        url = request.args.get('url')
        export_format = request.args.get('format', 'json')
        
        if not url:
            return jsonify({"error": "URL parameter is required"}), 400
        
        print(f"[API] Processing article via GET: {url}")
        
        # Process the article
        article = processor.extract_article(url)
        
        # Export to local file
        export_path = exporter.export_article(article, format=export_format)
        
        # Return processed data
        response = {
            "status": "success",
            "article": {
                "url": article.url,
                "title": article.title,
                "source_domain": article.source_domain,
                "published_date": article.published_date,
                "extracted_date": article.extracted_date,
                "word_count": article.word_count,
                "metadata": article.metadata
            },
            "export_path": export_path,
            "content_preview": article.content[:200] + "..." if len(article.content) > 200 else article.content
        }
        
        return jsonify(response)
        
    except Exception as e:
        print(f"[API] Error processing article: {str(e)}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


if __name__ == '__main__':
    print("Starting News Aggregator API...")
    app.run(debug=True, host='0.0.0.0', port=5000)