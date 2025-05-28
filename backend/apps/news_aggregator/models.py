from django.db import models
from django.contrib.postgres.fields import ArrayField
from apps.core.models import TimestampedModel, User
import uuid


class NewsSource(TimestampedModel):
    """
    Represents a news source/website
    """
    name = models.CharField(max_length=255)
    domain = models.CharField(max_length=255, unique=True)
    language = models.CharField(max_length=10, default='el')  # Greek by default
    is_active = models.BooleanField(default=True)
    requires_javascript = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'news_sources'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Article(TimestampedModel):
    """
    Represents a news article
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source = models.ForeignKey(NewsSource, on_delete=models.CASCADE, related_name='articles')
    url = models.URLField(unique=True, max_length=500)
    title = models.CharField(max_length=500)
    content = models.TextField()
    author = models.CharField(max_length=255, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    language = models.CharField(max_length=10, default='el')
    word_count = models.IntegerField(default=0)
    reading_time = models.IntegerField(default=0)  # in minutes
    
    # Processing status
    is_processed = models.BooleanField(default=False)
    is_enriched = models.BooleanField(default=False)
    processing_error = models.TextField(blank=True)
    
    class Meta:
        db_table = 'articles'
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['url']),
            models.Index(fields=['published_at']),
            models.Index(fields=['is_processed', 'is_enriched']),
        ]
    
    def __str__(self):
        return self.title


class AIAnalysis(TimestampedModel):
    """
    Stores AI analysis results for articles
    """
    ANALYSIS_TYPES = [
        ('jargon', 'Jargon Analysis'),
        ('viewpoints', 'Viewpoints Analysis'),
        ('fact_check', 'Fact Check'),
        ('bias', 'Bias Analysis'),
        ('timeline', 'Timeline Analysis'),
        ('expert', 'Expert Opinions'),
        ('x_pulse', 'X Pulse Analysis'),
    ]
    
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='analyses')
    analysis_type = models.CharField(max_length=20, choices=ANALYSIS_TYPES)
    result = models.JSONField()
    model_used = models.CharField(max_length=50, default='grok-3')
    processing_time = models.FloatField()  # in seconds
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'ai_analyses'
        unique_together = ['article', 'analysis_type']
        indexes = [
            models.Index(fields=['analysis_type']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_analysis_type_display()} - {self.article.title[:50]}"


class ProcessingJob(TimestampedModel):
    """
    Tracks article processing jobs
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='jobs')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    job_type = models.CharField(max_length=50)  # 'extraction', 'enrichment', etc.
    celery_task_id = models.CharField(max_length=255, blank=True)
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'processing_jobs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['celery_task_id']),
        ]
    
    def __str__(self):
        return f"{self.job_type} - {self.status}"