from django.db import migrations
from django.utils.text import slugify

def seed_categories(apps, schema_editor):
    Category = apps.get_model('products', 'Category')
    categories = ['Wedding', 'Silk', 'Designer']
    for name in categories:
        Category.objects.get_or_create(
            name=name,
            defaults={
                'slug': slugify(name),
                'description': f'{name} Collection'
            }
        )

def reverse_seed(apps, schema_editor):
    Category = apps.get_model('products', 'Category')
    Category.objects.filter(name__in=['Wedding', 'Silk', 'Designer']).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('products', '0002_rename_sku_product_item_code_product_video_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_categories, reverse_seed),
    ]
