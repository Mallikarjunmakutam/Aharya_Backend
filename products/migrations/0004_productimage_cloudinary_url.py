# Generated manually for Cloudinary URL storage

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0003_seed_categories'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productimage',
            name='image',
            field=models.URLField(blank=True, max_length=500),
        ),
    ]
