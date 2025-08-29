
from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator
from vouchers.models import Voucher

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    stock = models.PositiveIntegerField()
    image = models.ImageField(upload_to="products/product_images/", blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")

    def __str__(self):
        return self.name

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField(default=False)
    voucher = models.ForeignKey(Voucher,related_name='orders', null=True, blank=True, on_delete=models.SET_NULL)
    discount = models.IntegerField(default = 0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    stripe_checkout_session_id = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Order {self.id} - {self.user.username}"

    def total_amount(self):
        return sum((item.subtotal() for item in self.items.select_related('product')), Decimal('0'))

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    def subtotal(self):
        return (self.product.price or Decimal("0")) * self.quantity

class Wishlist(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    products = models.ManyToManyField(Product, blank=True)

    def __str__(self):
        return f"Wishlist for {self.user.username}"

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [ models.UniqueConstraint(fields=['user','product'], name='one_review_per_user_product')]

    def __str__(self):
        return f"{self.product.name} - {self.rating} stars"
