"""
Django management command to test article extraction only
Usage: python manage.py test_extraction <url>
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
import asyncio
import logging

from apps.news_aggregator.models import Article, NewsSource, ProcessingJob
from apps.news_aggregator.extractors.article import ArticleExtractor

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Test article extraction from URL (no AI analysis)'
    
    def add_arguments(self, parser):
        parser.add_argument('url', type=str, help='URL of the article to extract')
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force reprocessing even if article exists'
        )
    
    def handle(self, *args, **options):
        url = options['url']
        force = options['force']
        
        self.stdout.write(f"Testing extraction for: {url}")
        
        try:
            # Check if article already exists
            existing_article = Article.objects.filter(url=url).first()
            if existing_article and not force:
                self.stdout.write(
                    self.style.WARNING(f"Article already exists: {existing_article.id}")
                )
                self.stdout.write(f"Title: {existing_article.title}")
                self.stdout.write(f"Content length: {len(existing_article.content)} characters")
                return
            
            # Extract article
            self.stdout.write("Extracting article content...")
            article = asyncio.run(self._extract_article_simple(url))
            
            if article:
                self.stdout.write(
                    self.style.SUCCESS(f"Article extracted successfully!")
                )
                self.stdout.write(f"ID: {article.id}")
                self.stdout.write(f"Title: {article.title}")
                self.stdout.write(f"Author: {article.author}")
                self.stdout.write(f"Content length: {len(article.content)} characters")
                self.stdout.write(f"Word count: {article.word_count}")
            else:
                self.stdout.write(
                    self.style.ERROR("Failed to extract article")
                )
                
        except Exception as e:
            raise CommandError(f"Error extracting article: {str(e)}")
    
    async def _extract_article_simple(self, url: str) -> Article:
        """Extract article using sync Django operations"""
        extractor = ArticleExtractor()
        
        try:
            # Extract article data
            self.stdout.write("Fetching and parsing article...")
            article_data = await extractor.extract(url)
            
            if not article_data:
                raise Exception("Failed to extract article content")
            
            self.stdout.write("Saving to database...")
            
            # Get or create news source
            domain = self._get_domain_from_url(url)
            source, created = NewsSource.objects.get_or_create(
                domain=domain,
                defaults={
                    'name': domain,
                    'language': 'el',
                    'is_active': True
                }
            )
            
            if created:
                self.stdout.write(f"Created new source: {domain}")
            
            # Create article
            article = Article.objects.create(
                url=url,
                title=article_data.get('title', ''),
                content=article_data.get('content', ''),
                author=article_data.get('author', ''),
                published_at=article_data.get('published_at'),
                source=source,
                word_count=len(article_data.get('content', '').split()),
                reading_time=max(1, len(article_data.get('content', '').split()) // 200),
                is_processed=True
            )
            
            return article
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Extraction failed: {str(e)}")
            )
            raise
    
    def _get_domain_from_url(self, url: str) -> str:
        """Extract domain from URL"""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc.replace('www.', '')