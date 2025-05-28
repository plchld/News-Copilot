from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/articles/<str:article_id>/updates/', consumers.ArticleUpdateConsumer.as_asgi()),
    path('ws/processing/<str:task_id>/', consumers.ProcessingProgressConsumer.as_asgi()),
]