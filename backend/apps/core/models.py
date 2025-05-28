from django.db import models
from django.contrib.auth.models import AbstractUser


class TimestampedModel(models.Model):
    """
    Abstract base model with created and modified timestamps
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class User(AbstractUser):
    """
    Custom user model for future extensibility
    """
    email = models.EmailField(unique=True)
    is_premium = models.BooleanField(default=False)
    analysis_count = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'