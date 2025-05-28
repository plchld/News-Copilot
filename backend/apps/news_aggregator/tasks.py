"""
Celery tasks for news aggregator
"""
from celery import shared_task
from celery.utils.log import get_task_logger
import asyncio
from typing import Dict, Any, List
from django.utils import timezone

logger = get_task_logger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_article_task(self, url: str, user_id: int = None):
    """
    Process an article from URL
    
    Args:
        url: Article URL to process
        user_id: Optional user ID who initiated the processing
        
    Returns:
        Dict with article_id and status
    """
    from apps.news_aggregator.models import Article, NewsSource, ProcessingJob
    from apps.news_aggregator.extractors.article import ArticleExtractor
    
    logger.info(f"Processing article: {url}")
    
    # Create processing job
    job = ProcessingJob.objects.create(
        job_type='extraction',
        status='processing',
        celery_task_id=self.request.id,
        started_at=timezone.now()
    )
    
    try:
        # Check if article already exists
        existing = Article.objects.filter(url=url).first()
        if existing:
            logger.info(f"Article already exists: {existing.id}")
            job.article = existing
            job.status = 'completed'
            job.completed_at = timezone.now()
            job.save()
            return {
                "status": "exists",
                "article_id": str(existing.id),
                "is_processed": existing.is_processed,
                "is_enriched": existing.is_enriched
            }
        
        # Extract article using async extractor
        extractor = ArticleExtractor()
        article_data = asyncio.run(extractor.extract(url))
        
        if not article_data:
            raise Exception("Failed to extract article content")
        
        # Get or create news source
        from urllib.parse import urlparse
        domain = urlparse(url).netloc.replace('www.', '')
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
        
        logger.info(f"Article processed successfully: {article.id}")
        
        return {
            "status": "success",
            "article_id": str(article.id),
            "title": article.title
        }
        
    except Exception as e:
        logger.error(f"Error processing article: {str(e)}")
        
        # Update job
        job.status = 'failed'
        job.error_message = str(e)
        job.completed_at = timezone.now()
        job.save()
        
        # Retry the task
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=2, default_retry_delay=120)
def analyze_article_task(self, article_id: str, analysis_types: List[str], user_id: int = None):
    """
    Run AI analysis on an article
    
    Args:
        article_id: ID of the article to analyze
        analysis_types: List of analysis types to run
        user_id: Optional user ID who initiated the analysis
        
    Returns:
        Dict with analysis results
    """
    from apps.news_aggregator.models import Article, AIAnalysis, ProcessingJob
    from apps.news_aggregator.agents.coordinator import AgentCoordinator
    
    logger.info(f"Analyzing article {article_id} with types: {analysis_types}")
    
    # Get article
    try:
        article = Article.objects.get(id=article_id)
    except Article.DoesNotExist:
        logger.error(f"Article {article_id} not found")
        return {"status": "error", "error": "Article not found"}
    
    # Create processing job
    job = ProcessingJob.objects.create(
        article=article,
        job_type='enrichment',
        status='processing',
        celery_task_id=self.request.id,
        started_at=timezone.now()
    )
    
    try:
        # Run analysis
        coordinator = AgentCoordinator()
        results = asyncio.run(
            coordinator.analyze_article(
                article_content=article.content,
                article_id=str(article.id),
                analysis_types=analysis_types
            )
        )
        
        # Save results
        successful_analyses = []
        failed_analyses = []
        
        for agent_name, result in results.items():
            if result.success and result.data:
                # Save to database
                analysis, created = AIAnalysis.objects.update_or_create(
                    article=article,
                    analysis_type=agent_name,
                    defaults={
                        'result': result.data,
                        'model_used': result.model_used.value if result.model_used else 'grok-3',
                        'processing_time': result.execution_time_ms / 1000.0 if result.execution_time_ms else 0
                    }
                )
                successful_analyses.append(agent_name)
            else:
                failed_analyses.append({
                    'agent': agent_name,
                    'error': result.error
                })
        
        # Mark article as enriched if at least one analysis succeeded
        if successful_analyses:
            article.is_enriched = True
            article.save()
        
        # Update job
        job.status = 'completed' if successful_analyses else 'failed'
        job.completed_at = timezone.now()
        if failed_analyses:
            job.error_message = f"Failed analyses: {failed_analyses}"
        job.save()
        
        logger.info(f"Analysis completed for article {article_id}: "
                   f"{len(successful_analyses)} successful, {len(failed_analyses)} failed")
        
        return {
            "status": "success",
            "article_id": str(article.id),
            "successful_analyses": successful_analyses,
            "failed_analyses": failed_analyses
        }
        
    except Exception as e:
        logger.error(f"Error analyzing article: {str(e)}")
        
        # Update job
        job.status = 'failed'
        job.error_message = str(e)
        job.completed_at = timezone.now()
        job.save()
        
        # Retry the task with lower complexity models
        raise self.retry(exc=e)


@shared_task
def cleanup_old_jobs():
    """
    Periodic task to clean up old processing jobs
    """
    from apps.news_aggregator.models import ProcessingJob
    from datetime import timedelta
    
    # Delete completed jobs older than 7 days
    cutoff_date = timezone.now() - timedelta(days=7)
    deleted_count = ProcessingJob.objects.filter(
        status='completed',
        created_at__lt=cutoff_date
    ).delete()[0]
    
    logger.info(f"Cleaned up {deleted_count} old processing jobs")
    
    return {"deleted_count": deleted_count}