from django.db import models
from django.conf import settings
from products.models import Product

class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart of {self.user.email}"

    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())

from products.models import Product, ProductVariant

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        color = f" ({self.variant.color_name})" if self.variant else ""
        return f"{self.quantity} x {self.product.name}{color}"

    @property
    def total_price(self):
        if self.variant:
            price = self.variant.discount_price if (self.variant.discount_price and self.variant.discount_price > 0) else self.variant.price
            if price is None:
                price = self.product.discount_price if self.product.discount_price else self.product.price
        else:
            price = self.product.discount_price if self.product.discount_price else self.product.price
        return price * self.quantity


class Wishlist(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlist')
    products = models.ManyToManyField(Product, related_name='wishlisted_by', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Wishlist of {self.user.email}"
