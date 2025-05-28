from rest_framework import serializers
from apps.news_aggregator.models import Article, NewsSource, AIAnalysis, ProcessingJob


class NewsSourceSerializer(serializers.ModelSerializer):
    article_count = serializers.SerializerMethodField()
    
    class Meta:
        model = NewsSource
        fields = [
            'id', 'name', 'domain', 'language', 
            'is_active', 'requires_javascript',
            'article_count', 'created_at'
        ]
    
    def get_article_count(self, obj):
        return obj.articles.count()


class AIAnalysisSerializer(serializers.ModelSerializer):
    analysis_type_display = serializers.CharField(source='get_analysis_type_display', read_only=True)
    
    class Meta:
        model = AIAnalysis
        fields = [
            'id', 'analysis_type', 'analysis_type_display',
            'result', 'model_used', 'processing_time',
            'created_at', 'created_by'
        ]


class ArticleSerializer(serializers.ModelSerializer):
    source_name = serializers.CharField(source='source.name', read_only=True)
    analyses = AIAnalysisSerializer(many=True, read_only=True)
    analysis_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Article
        fields = [
            'id', 'url', 'title', 'content', 'author',
            'published_at', 'source', 'source_name',
            'language', 'word_count', 'reading_time',
            'is_processed', 'is_enriched', 'processing_error',
            'analyses', 'analysis_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'word_count', 'reading_time',
            'is_processed', 'is_enriched',
            'created_at', 'updated_at'
        ]
    
    def get_analysis_count(self, obj):
        return obj.analyses.count()


class ArticleListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for article lists
    """
    source_name = serializers.CharField(source='source.name', read_only=True)
    
    class Meta:
        model = Article
        fields = [
            'id', 'url', 'title', 'author',
            'published_at', 'source_name',
            'is_processed', 'is_enriched',
            'created_at'
        ]


class ProcessingJobSerializer(serializers.ModelSerializer):
    article_title = serializers.CharField(source='article.title', read_only=True)
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = ProcessingJob
        fields = [
            'id', 'article', 'article_title',
            'status', 'job_type', 'celery_task_id',
            'error_message', 'started_at', 'completed_at',
            'duration', 'created_at'
        ]
    
    def get_duration(self, obj):
        if obj.started_at and obj.completed_at:
            delta = obj.completed_at - obj.started_at
            return delta.total_seconds()
        return None


class ProcessArticleRequestSerializer(serializers.Serializer):
    url = serializers.URLField(required=True)
    force_refresh = serializers.BooleanField(default=False)


class AnalyzeArticleRequestSerializer(serializers.Serializer):
    article_id = serializers.UUIDField(required=True)
    types = serializers.ListField(
        child=serializers.ChoiceField(choices=[
            'jargon', 'viewpoints', 'fact_check',
            'bias', 'timeline', 'expert', 'x_pulse', 'all'
        ]),
        default=['all']
    )