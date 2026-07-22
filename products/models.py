import uuid
from django.db import models
from django.utils.text import slugify

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    subcategory = models.CharField(max_length=100, blank=True)
    description = models.TextField()
    fabric = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    stock = models.IntegerField(default=0)
    item_code = models.CharField(max_length=50, unique=True)
    video = models.FileField(upload_to='products/videos/', blank=True, null=True)
    rating = models.FloatField(default=0)
    total_reviews = models.IntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        
        is_stock_update = False
        if self.pk:
            try:
                orig = Product.objects.get(pk=self.pk)
                if orig.stock != self.stock:
                    is_stock_update = True
            except Product.DoesNotExist:
                pass

        super().save(*args, **kwargs)

        if is_stock_update:
            first_variant = self.variants.first()
            if first_variant and first_variant.stock != self.stock:
                first_variant.stock = self.stock
                super(ProductVariant, first_variant).save()

    def __str__(self):
        return self.name

class ProductVariant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    color_name = models.CharField(max_length=100)
    color_code = models.CharField(max_length=7, blank=True) # e.g. #FFFFFF or hex
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    stock = models.IntegerField(default=0)
    sku = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        parent_product = self.product
        parent_product.stock = sum(v.stock for v in parent_product.variants.all())
        parent_product.save(update_fields=['stock'])

    def delete(self, *args, **kwargs):
        parent_product = self.product
        super().delete(*args, **kwargs)
        parent_product.stock = sum(v.stock for v in parent_product.variants.all())
        parent_product.save(update_fields=['stock'])

    def __str__(self):
        return f"{self.product.name} - {self.color_name} ({self.sku})"

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images_deprecated', null=True, blank=True)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='images', null=True, blank=True)
    image = models.URLField(max_length=500, blank=True)
    is_main = models.BooleanField(default=False)
    alt_text = models.CharField(max_length=255, blank=True)

    def __str__(self):
        name = self.variant.product.name if self.variant else (self.product.name if self.product else "Unknown")
        return f"Image for {name}"


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user_name = models.CharField(max_length=100) # Simple reviews or link to User?
    rating = models.IntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review for {self.product.name} by {self.user_name}"
