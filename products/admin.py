from django import forms
from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, ProductImage, Review
from .cloudinary_utils import upload_product_image, delete_cloudinary_image


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    prepopulated_fields = {'slug': ('name',)}


class ProductImageInlineForm(forms.ModelForm):
    upload = forms.ImageField(required=False, label='Upload image')

    class Meta:
        model = ProductImage
        fields = ['upload', 'is_main', 'alt_text']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and self.instance.image:
            self.fields['upload'].help_text = 'Leave empty to keep the current Cloudinary image.'

    def clean(self):
        cleaned_data = super().clean()
        upload = cleaned_data.get('upload')
        if not self.instance.pk and not upload:
            raise forms.ValidationError('An image file is required for new product images.')
        if self.instance.pk and not upload and not self.instance.image:
            raise forms.ValidationError('An image file is required.')
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        upload = self.cleaned_data.get('upload')
        if upload:
            if instance.pk and instance.image:
                delete_cloudinary_image(instance.image)
            product_id = instance.product_id or self.cleaned_data.get('product').pk
            instance.image = upload_product_image(upload, str(product_id))
        elif not instance.pk:
            raise forms.ValidationError('An image file is required for new product images.')

        if commit:
            instance.save()
        return instance


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    form = ProductImageInlineForm
    extra = 1
    fields = ['upload', 'is_main', 'alt_text', 'image_preview']
    readonly_fields = ['image_preview']

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: cover;" />',
                obj.image,
            )
        return 'No image'

    image_preview.short_description = 'Preview'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock', 'is_featured', 'is_active', 'image_preview']
    list_filter = ['category', 'is_featured', 'is_active', 'created_at', 'fabric']
    search_fields = ['name', 'item_code', 'description']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline]
    list_editable = ['price', 'stock', 'is_featured', 'is_active']

    def image_preview(self, obj):
        main_image = obj.images.filter(is_main=True).first()
        if not main_image:
            main_image = obj.images.first()
        if main_image:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: cover;" />',
                main_image.image,
            )
        return 'No Image'

    image_preview.short_description = 'Preview'


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user_name', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['product__name', 'user_name', 'comment']
