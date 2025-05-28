from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from apps.news_aggregator.models import Article, NewsSource, AIAnalysis
from .serializers import ArticleSerializer, NewsSourceSerializer, AIAnalysisSerializer
from apps.news_aggregator.tasks import process_article_task, analyze_article_task


class ArticleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Article CRUD operations
    """
    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticated]
    
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


class NewsSourceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for NewsSource CRUD operations
    """
    queryset = NewsSource.objects.filter(is_active=True)
    serializer_class = NewsSourceSerializer
    permission_classes = [IsAuthenticated]


class AIAnalysisViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing AI analyses
    """
    queryset = AIAnalysis.objects.all()
    serializer_class = AIAnalysisSerializer
    permission_classes = [IsAuthenticated]
    
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
@permission_classes([IsAuthenticated])
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
    
    # Queue processing task
    task = process_article_task.delay(url, request.user.id)
    
    return Response({
        'task_id': task.id,
        'message': 'Article processing started',
        'status_url': f'/api/v1/tasks/{task.id}/status/'
    }, status=status.HTTP_202_ACCEPTED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
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
    
    # Queue analysis task
    task = analyze_article_task.delay(
        str(article.id),
        analysis_types,
        request.user.id
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
    return Response({
        'status': 'healthy',
        'service': 'News Copilot API',
        'version': '2.0.0'
    })