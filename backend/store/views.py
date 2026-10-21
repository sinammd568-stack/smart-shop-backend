from rest_framework import viewsets, permissions
from .models import Product, Order, User
from .serializers import ProductSerializer, OrderSerializer, UserSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    # فقط ادمین‌ها بتونن کاربر (فروشنده) جدید بسازن
    def get_permissions(self):
        if self.action in ['list', 'create', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().order_by('-created_at')
    serializer_class = ProductSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()] # فقط لاگین کرده‌ها (ادمین یا فروشنده) می‌تونن محصول بسازن

    # وقتی محصول جدید ساخته میشه، خودکار به اسم کاربری که لاگین کرده ثبت میشه
    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().order_by('-created_at')
    serializer_class = OrderSerializer
    permission_classes = [permissions.AllowAny]
