"""
Django management command to process articles
Usage: python manage.py process_article <url>
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
import asyncio
import logging

from apps.news_aggregator.models import Article, NewsSource, ProcessingJob
from apps.news_aggregator.extractors.article import ArticleExtractor
from apps.news_aggregator.agents.coordinator import AgentCoordinator

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Process a news article from URL'
    
    def add_arguments(self, parser):
        parser.add_argument('url', type=str, help='URL of the article to process')
        parser.add_argument(
            '--analyze',
            action='store_true',
            help='Run AI analysis after extraction'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force reprocessing even if article exists'
        )
    
    def handle(self, *args, **options):
        url = options['url']
        analyze = options['analyze']
        force = options['force']
        
        self.stdout.write(f"Processing article: {url}")
        
        try:
            # Check if article already exists
            existing_article = Article.objects.filter(url=url).first()
            if existing_article and not force:
                self.stdout.write(
                    self.style.WARNING(f"Article already exists: {existing_article.id}")
                )
                if analyze and not existing_article.is_enriched:
                    self.stdout.write("Running analysis on existing article...")
                    asyncio.run(self._analyze_article(existing_article))
                return
            
            # Extract article
            self.stdout.write("Extracting article content...")
            article = asyncio.run(self._extract_article(url))
            
            if article:
                self.stdout.write(
                    self.style.SUCCESS(f"Article extracted successfully: {article.id}")
                )
                
                if analyze:
                    self.stdout.write("Running AI analysis...")
                    asyncio.run(self._analyze_article(article))
            else:
                self.stdout.write(
                    self.style.ERROR("Failed to extract article")
                )
                
        except Exception as e:
            raise CommandError(f"Error processing article: {str(e)}")
    
    async def _extract_article(self, url: str) -> Article:
        """Extract article using the article extractor"""
        extractor = ArticleExtractor()
        
        # Create processing job
        job = ProcessingJob.objects.create(
            article=None,  # Will be updated after extraction
            job_type='extraction',
            status='processing',
            started_at=timezone.now()
        )
        
        try:
            # Extract article data
            article_data = await extractor.extract(url)
            
            if not article_data:
                raise Exception("Failed to extract article content")
            
            # Get or create news source
            domain = self._get_domain_from_url(url)
            source, _ = NewsSource.objects.get_or_create(
                domain=domain,
                defaults={
                    'name': domain,
                    'language': 'el',
                    'is_active': True
                }
            )
            
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
            
            # Update job
            job.article = article
            job.status = 'completed'
            job.completed_at = timezone.now()
            job.save()
            
            return article
            
        except Exception as e:
            # Update job with error
            job.status = 'failed'
            job.error_message = str(e)
            job.completed_at = timezone.now()
            job.save()
            raise
    
    async def _analyze_article(self, article: Article):
        """Run AI analysis on the article"""
        coordinator = AgentCoordinator()
        
        # Create processing job
        job = ProcessingJob.objects.create(
            article=article,
            job_type='enrichment',
            status='processing',
            started_at=timezone.now()
        )
        
        try:
            # Run all analyses
            results = await coordinator.analyze_article(
                article_content=article.content,
                article_id=str(article.id)
            )
            
            # Save results
            for agent_name, result in results.items():
                if result.success and result.data:
                    from apps.news_aggregator.models import AIAnalysis
                    
                    AIAnalysis.objects.update_or_create(
                        article=article,
                        analysis_type=agent_name,
                        defaults={
                            'result': result.data,
                            'model_used': result.model_used.value if result.model_used else 'grok-3',
                            'processing_time': result.execution_time_ms / 1000.0 if result.execution_time_ms else 0
                        }
                    )
            
            # Mark article as enriched
            article.is_enriched = True
            article.save()
            
            # Update job
            job.status = 'completed'
            job.completed_at = timezone.now()
            job.save()
            
            self.stdout.write(
                self.style.SUCCESS(f"Analysis completed for article: {article.id}")
            )
            
        except Exception as e:
            # Update job with error
            job.status = 'failed'
            job.error_message = str(e)
            job.completed_at = timezone.now()
            job.save()
            
            self.stdout.write(
                self.style.ERROR(f"Analysis failed: {str(e)}")
            )
    
    def _get_domain_from_url(self, url: str) -> str:
        """Extract domain from URL"""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc.replace('www.', '')