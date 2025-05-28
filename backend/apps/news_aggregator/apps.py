from django.apps import AppConfig


class NewsAggregatorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.news_aggregator'
    verbose_name = 'News Aggregator'
    
    def ready(self):
        # Import signal handlers
        try:
            import apps.news_aggregator.signals
        except ImportError:
            pass