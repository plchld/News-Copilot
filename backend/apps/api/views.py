import os
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.conf import settings
from apps.news_aggregator.models import Article, NewsSource, AIAnalysis
from .serializers import ArticleSerializer, NewsSourceSerializer, AIAnalysisSerializer
from .permissions import IsAuthenticatedOrOptional, NoAuthRequiredPermission
from apps.news_aggregator.tasks import process_article_task, analyze_article_task


class ArticleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Article CRUD operations
    """
    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticatedOrOptional]
    
    def get_queryset(self):
        queryset = Article.objects.all()
        
        # Filter by source
        source_id = self.request.query_params.get('source')
        if source_id:
            queryset = queryset.filter(source_id=source_id)
        
        # Filter by processing status
        is_processed = self.request.query_params.get('is_processed')
        if is_processed is not None:
            queryset = queryset.filter(is_processed=is_processed.lower() == 'true')
        
        # Filter by enrichment status
        is_enriched = self.request.query_params.get('is_enriched')
        if is_enriched is not None:
            queryset = queryset.filter(is_enriched=is_enriched.lower() == 'true')
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def analyses(self, request, pk=None):
        """Get all analyses for an article"""
        article = self.get_object()
        analyses = article.analyses.all()
        serializer = AIAnalysisSerializer(analyses, many=True)
        return Response(serializer.data)


class NewsSourceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing news sources
    """
    queryset = NewsSource.objects.all()
    serializer_class = NewsSourceSerializer
    permission_classes = [IsAuthenticatedOrOptional]


class AIAnalysisViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing AI analyses
    """
    queryset = AIAnalysis.objects.all()
    serializer_class = AIAnalysisSerializer
    permission_classes = [IsAuthenticatedOrOptional]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by article
        article_id = self.request.query_params.get('article')
        if article_id:
            queryset = queryset.filter(article_id=article_id)
        
        # Filter by analysis type
        analysis_type = self.request.query_params.get('type')
        if analysis_type:
            queryset = queryset.filter(analysis_type=analysis_type)
        
        return queryset


@api_view(['POST'])
@permission_classes([IsAuthenticatedOrOptional])
def process_article(request):
    """
    Process a new article from URL
    """
    url = request.data.get('url')
    if not url:
        return Response(
            {'error': 'URL is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if article already exists
    existing_article = Article.objects.filter(url=url).first()
    if existing_article:
        return Response({
            'article_id': str(existing_article.id),
            'message': 'Article already exists',
            'is_processed': existing_article.is_processed,
            'is_enriched': existing_article.is_enriched
        })
    
    # Get user ID (or use None if auth is not required)
    user_id = None
    auth_required = os.getenv('AUTH_REQUIRED', 'true').lower() == 'true'
    
    if auth_required and hasattr(request, 'user') and request.user.is_authenticated:
        user_id = request.user.id
    elif not auth_required:
        # When auth is not required, we can proceed without a user
        user_id = None
    
    # Queue processing task
    task = process_article_task.delay(url, user_id)
    
    return Response({
        'task_id': task.id,
        'message': 'Article processing started',
        'status_url': f'/api/v1/tasks/{task.id}/status/'
    }, status=status.HTTP_202_ACCEPTED)


@api_view(['POST'])
@permission_classes([IsAuthenticatedOrOptional])
def analyze_article(request):
    """
    Run AI analysis on an article
    """
    article_id = request.data.get('article_id')
    analysis_types = request.data.get('types', ['all'])
    
    if not article_id:
        return Response(
            {'error': 'article_id is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    article = get_object_or_404(Article, id=article_id)
    
    # Get user ID (or use None if auth is not required)
    user_id = None
    auth_required = os.getenv('AUTH_REQUIRED', 'true').lower() == 'true'
    
    if auth_required and hasattr(request, 'user') and request.user.is_authenticated:
        user_id = request.user.id
    elif not auth_required:
        # When auth is not required, we can proceed without a user
        user_id = None
    
    # Queue analysis task
    task = analyze_article_task.delay(
        str(article.id),
        analysis_types,
        user_id
    )
    
    return Response({
        'task_id': task.id,
        'message': 'Analysis started',
        'status_url': f'/api/v1/tasks/{task.id}/status/'
    }, status=status.HTTP_202_ACCEPTED)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint
    """
    auth_required = os.getenv('AUTH_REQUIRED', 'true').lower() == 'true'
    
    return Response({
        'status': 'healthy',
        'auth_required': auth_required,
        'debug': settings.DEBUG,
        'message': 'News Copilot API is running'
    })


@api_view(['GET'])
@permission_classes([NoAuthRequiredPermission])
def testing_info(request):
    """
    Testing mode information endpoint (only available when AUTH_REQUIRED=false)
    """
    return Response({
        'auth_required': False,
        'message': 'Authentication is disabled - API endpoints are open for testing',
        'available_endpoints': [
            'POST /api/process/ - Process article',
            'POST /api/analyze/ - Analyze article',
            'GET /api/articles/ - List articles',
            'GET /api/articles/{id}/ - Get article details',
            'GET /api/articles/{id}/analyses/ - Get article analyses',
            'GET /api/health/ - Health check',
            'GET /api/testing-info/ - This endpoint'
        ]
    })