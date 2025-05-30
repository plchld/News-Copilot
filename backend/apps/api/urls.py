from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import admin_views

app_name = 'api'

router = DefaultRouter()
router.register(r'articles', views.ArticleViewSet, basename='article')
router.register(r'sources', views.NewsSourceViewSet, basename='source')
router.register(r'analyses', views.AIAnalysisViewSet, basename='analysis')

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    
    # Custom endpoints
    path('process/', views.process_article, name='process_article'),
    path('analyze/', views.analyze_article, name='analyze_article'),
    path('health/', views.health_check, name='health_check'),
    path('testing-info/', views.testing_info, name='testing_info'),
    
    # Admin endpoints
    path('admin/stats/', admin_views.admin_stats, name='admin_stats'),
    path('admin/users/', admin_views.user_list, name='admin_users'),
]