"""
WebSocket consumers for real-time updates
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.cache import cache

logger = logging.getLogger(__name__)


class ArticleUpdateConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for article processing updates
    """
    
    async def connect(self):
        self.article_id = self.scope['url_route']['kwargs']['article_id']
        self.room_group_name = f'article_{self.article_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial status
        await self.send_article_status()
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'get_status':
                await self.send_article_status()
            
        except json.JSONDecodeError:
            await self.send(json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
    
    async def article_update(self, event):
        """Handle article update events from channel layer"""
        await self.send(json.dumps({
            'type': 'article_update',
            'data': event['data']
        }))
    
    async def analysis_progress(self, event):
        """Handle analysis progress events"""
        await self.send(json.dumps({
            'type': 'analysis_progress',
            'data': event['data']
        }))
    
    @database_sync_to_async
    def get_article_status(self):
        """Get current article status from database"""
        from apps.news_aggregator.models import Article
        
        try:
            article = Article.objects.get(id=self.article_id)
            return {
                'id': str(article.id),
                'is_processed': article.is_processed,
                'is_enriched': article.is_enriched,
                'analyses': list(article.analyses.values_list('analysis_type', flat=True))
            }
        except Article.DoesNotExist:
            return None
    
    async def send_article_status(self):
        """Send current article status to client"""
        status = await self.get_article_status()
        
        if status:
            await self.send(json.dumps({
                'type': 'status',
                'data': status
            }))
        else:
            await self.send(json.dumps({
                'type': 'error',
                'message': 'Article not found'
            }))


class ProcessingProgressConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for processing task progress
    """
    
    async def connect(self):
        self.task_id = self.scope['url_route']['kwargs']['task_id']
        self.room_group_name = f'task_{self.task_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial task status
        await self.send_task_status()
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def task_progress(self, event):
        """Handle task progress updates"""
        await self.send(json.dumps({
            'type': 'progress',
            'data': event['data']
        }))
    
    async def task_complete(self, event):
        """Handle task completion"""
        await self.send(json.dumps({
            'type': 'complete',
            'data': event['data']
        }))
    
    async def task_failed(self, event):
        """Handle task failure"""
        await self.send(json.dumps({
            'type': 'failed',
            'data': event['data']
        }))
    
    def get_task_status_from_cache(self):
        """Get task status from cache"""
        return cache.get(f'task_status:{self.task_id}')
    
    async def send_task_status(self):
        """Send current task status to client"""
        status = await database_sync_to_async(self.get_task_status_from_cache)()
        
        if status:
            await self.send(json.dumps({
                'type': 'status',
                'data': status
            }))
        else:
            # Try to get from Celery
            from celery.result import AsyncResult
            result = AsyncResult(self.task_id)
            
            await self.send(json.dumps({
                'type': 'status',
                'data': {
                    'state': result.state,
                    'info': result.info if isinstance(result.info, dict) else str(result.info)
                }
            }))