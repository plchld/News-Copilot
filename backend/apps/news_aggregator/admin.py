from django.contrib import admin
from .models import NewsSource, Article, AIAnalysis, ProcessingJob


@admin.register(NewsSource)
class NewsSourceAdmin(admin.ModelAdmin):
    list_display = ['name', 'domain', 'language', 'is_active', 'requires_javascript']
    list_filter = ['is_active', 'requires_javascript', 'language']
    search_fields = ['name', 'domain']
    ordering = ['name']


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'source', 'published_at', 'is_processed', 'is_enriched']
    list_filter = ['is_processed', 'is_enriched', 'source', 'published_at']
    search_fields = ['title', 'url', 'content']
    readonly_fields = ['id', 'created_at', 'updated_at', 'word_count', 'reading_time']
    date_hierarchy = 'published_at'
    ordering = ['-published_at']


@admin.register(AIAnalysis)
class AIAnalysisAdmin(admin.ModelAdmin):
    list_display = ['article', 'analysis_type', 'model_used', 'processing_time', 'created_at']
    list_filter = ['analysis_type', 'model_used', 'created_at']
    search_fields = ['article__title']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(ProcessingJob)
class ProcessingJobAdmin(admin.ModelAdmin):
    list_display = ['id', 'article', 'job_type', 'status', 'created_at']
    list_filter = ['status', 'job_type', 'created_at']
    search_fields = ['article__title', 'celery_task_id']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-created_at']