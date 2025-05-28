"""
Django management command to process articles
Usage: python manage.py process_article <url>
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
import asyncio
import logging

from apps.news_aggregator.models import Article, NewsSource, ProcessingJob
from apps.news_aggregator.extractors.article import ArticleExtractor, EnhancedArticleExtractor
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
        parser.add_argument(
            '--enhanced',
            action='store_true',
            help='Use enhanced Selenium extractor for JavaScript sites'
        )
    
    def handle(self, *args, **options):
        url = options['url']
        analyze = options['analyze']
        force = options['force']
        enhanced = options['enhanced']
        
        self.stdout.write(f"Processing article: {url}")
        
        try:
            # Check if article already exists (sync operation)
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
            extractor_type = "Enhanced Selenium" if enhanced else "Basic"
            self.stdout.write(f"Extracting article content using {extractor_type} extractor...")
            article = asyncio.run(self._extract_article(url, enhanced))
            
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
    
    async def _extract_article(self, url: str, enhanced: bool = False) -> Article:
        """Extract article using the article extractor"""
        from asgiref.sync import sync_to_async
        
        # Choose extractor based on enhanced flag or URL domain
        if enhanced:
            extractor = EnhancedArticleExtractor()
            self.stdout.write("Using Enhanced Selenium extractor...")
        else:
            # Auto-detect if we need enhanced extraction for JavaScript sites
            js_sites = ['amna.gr', 'cnn.gr', 'skai.gr', 'ant1news.gr', 'star.gr', 'real.gr']
            if any(site in url for site in js_sites):
                extractor = EnhancedArticleExtractor()
                self.stdout.write("Auto-detected JavaScript site, using Enhanced Selenium extractor...")
            else:
                extractor = ArticleExtractor()
                self.stdout.write("Using basic extractor...")
        
        # Create processing job (sync operation)
        job = await sync_to_async(ProcessingJob.objects.create)(
            article=None,  # Will be updated after extraction
            url=url,  # Track URL even if extraction fails
            job_type='extraction',
            status='processing',
            started_at=timezone.now()
        )
        
        try:
            # Extract article data
            article_data = await extractor.extract(url)
            
            if not article_data:
                raise Exception("Failed to extract article content")
            
            # Get or create news source (sync operation)
            domain = self._get_domain_from_url(url)
            source, _ = await sync_to_async(NewsSource.objects.get_or_create)(
                domain=domain,
                defaults={
                    'name': domain,
                    'language': 'el',
                    'is_active': True
                }
            )
            
            # Create article (sync operation)
            article = await sync_to_async(Article.objects.create)(
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
            
            # Update job (sync operation)
            job.article = article
            job.status = 'completed'
            job.completed_at = timezone.now()
            await sync_to_async(job.save)()
            
            # Clean up enhanced extractor if used
            if hasattr(extractor, 'close'):
                extractor.close()
            
            return article
            
        except Exception as e:
            # Clean up enhanced extractor if used
            if hasattr(extractor, 'close'):
                extractor.close()
                
            # Update job with error (sync operation)
            job.status = 'failed'
            job.error_message = str(e)
            job.completed_at = timezone.now()
            await sync_to_async(job.save)()
            raise
    
    async def _analyze_article(self, article: Article):
        """Run AI analysis on the article"""
        from asgiref.sync import sync_to_async
        coordinator = AgentCoordinator()
        
        # Create processing job (sync operation)
        job = await sync_to_async(ProcessingJob.objects.create)(
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
            
            # Save results (sync operations)
            from apps.news_aggregator.models import AIAnalysis
            for agent_name, result in results.items():
                if result.success and result.data:
                    await sync_to_async(AIAnalysis.objects.update_or_create)(
                        article=article,
                        analysis_type=agent_name,
                        defaults={
                            'result': result.data,
                            'model_used': result.model_used.value if result.model_used else 'grok-3',
                            'processing_time': result.execution_time_ms / 1000.0 if result.execution_time_ms else 0
                        }
                    )
            
            # Mark article as enriched (sync operation)
            article.is_enriched = True
            await sync_to_async(article.save)()
            
            # Update job (sync operation)
            job.status = 'completed'
            job.completed_at = timezone.now()
            await sync_to_async(job.save)()
            
            self.stdout.write(
                self.style.SUCCESS(f"Analysis completed for article: {article.id}")
            )
            
        except Exception as e:
            # Update job with error (sync operation)
            job.status = 'failed'
            job.error_message = str(e)
            job.completed_at = timezone.now()
            await sync_to_async(job.save)()
            
            self.stdout.write(
                self.style.ERROR(f"Analysis failed: {str(e)}")
            )
    
    def _get_domain_from_url(self, url: str) -> str:
        """Extract domain from URL"""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc.replace('www.', '')