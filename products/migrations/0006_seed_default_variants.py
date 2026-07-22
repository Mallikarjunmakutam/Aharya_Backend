import uuid
from django.db import migrations

def create_default_variants(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    ProductVariant = apps.get_model('products', 'ProductVariant')
    ProductImage = apps.get_model('products', 'ProductImage')

    for product in Product.objects.all():
        if not ProductVariant.objects.filter(product=product).exists():
            variant = ProductVariant.objects.create(
                product=product,
                color_name="Original",
                color_code="#E5E7EB", # Neutral Light Gray
                price=product.price,
                discount_price=product.discount_price,
                stock=product.stock,
                sku=product.item_code
            )
            # Update all images for this product to point to the default variant
            images = ProductImage.objects.filter(product=product)
            for image in images:
                image.variant = variant
                image.save()

def rollback_default_variants(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('products', '0005_alter_productimage_product_productvariant_and_more'),
    ]

    operations = [
        migrations.RunPython(create_default_variants, rollback_default_variants),
    ]
