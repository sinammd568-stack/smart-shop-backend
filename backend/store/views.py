from rest_framework import viewsets, permissions
from .models import Product, Order
from .serializers import ProductSerializer, OrderSerializer

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().order_by('-created_at')
    serializer_class = ProductSerializer
    # فقط ادمین‌ها اجازه تغییر دارن، بقیه فقط می‌تونن ببینن
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().order_by('-created_at')
    serializer_class = OrderSerializer
    # فعلاً برای اینکه کاربر بتونه سفارش ثبت کنه، اجازه آزاد می‌ذاریم
    permission_classes = [permissions.AllowAny]
