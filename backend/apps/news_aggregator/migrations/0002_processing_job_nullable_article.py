# Generated migration for ProcessingJob article nullable field

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('news_aggregator', '0001_initial'),  # Update with actual latest migration
    ]

    operations = [
        migrations.AlterField(
            model_name='processingjob',
            name='article',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='jobs', to='news_aggregator.article'),
        ),
        migrations.AddField(
            model_name='processingjob',
            name='url',
            field=models.URLField(blank=True, max_length=500),
        ),
    ]
