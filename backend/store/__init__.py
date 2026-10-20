from django.db import models
from django.contrib.auth.models import AbstractUser

# ۱. تعریف کاربر سفارشی (برای اینکه بتونیم نقش فروشنده و ادمین داشته باشیم)
class User(AbstractUser):
    is_seller = models.BooleanField(default=False)
    phone = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return self.username

# ۲. مدل محصولات
class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.PositiveIntegerField() # قیمت به تومان
    old_price = models.PositiveIntegerField(blank=True, null=True) # برای تخفیف
    category = models.CharField(max_length=50)
    image = models.URLField() # لینک عکس محصول
    tag = models.CharField(max_length=50, blank=True) # مثل: پرفروش، جدید
    rating = models.FloatField(default=4.5)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# ۳. مدل سفارشات
class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'در انتظار پرداخت'),
        ('processing', 'در حال پردازش'),
        ('shipped', 'در حال ارسال'),
        ('delivered', 'تحویل شده'),
        ('canceled', 'لغو شده'),
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True) # کاربر (اگه لاگین باشه)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    total_price = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.id} - {self.status}"

# ۴. آیتم‌های داخل سفارش (چی چی خریده شده)
class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    price = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.name if self.product else 'Deleted Product'}"
