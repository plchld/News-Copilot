from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from apps.news_aggregator.models import Article, AIAnalysis
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_stats(request):
    """
    Get admin dashboard statistics
    """
    # Get counts
    total_users = User.objects.count()
    total_articles = Article.objects.count()
    total_analyses = AIAnalysis.objects.count()
    
    # Get recent activity (last 7 days)
    seven_days_ago = timezone.now() - timedelta(days=7)
    recent_articles = Article.objects.filter(
        created_at__gte=seven_days_ago
    ).order_by('-created_at')[:10]
    
    recent_activity = []
    for article in recent_articles:
        recent_activity.append({
            'id': str(article.id),
            'type': 'article',
            'description': f'New article: {article.title[:50]}...',
            'timestamp': article.created_at.isoformat()
        })
    
    return Response({
        'total_users': total_users,
        'total_articles': total_articles,
        'total_analyses': total_analyses,
        'recent_activity': recent_activity
    })


@api_view(['GET'])
@permission_classes([IsAdminUser])
def user_list(request):
    """
    Get list of all users (admin only)
    """
    users = User.objects.all().order_by('-date_joined')
    user_data = []
    
    for user in users:
        user_data.append({
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_active': user.is_active,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'date_joined': user.date_joined.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None
        })
    
    return Response(user_data)