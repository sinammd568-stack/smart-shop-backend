from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Sum, F, IntegerField
from .models import Product, Order, User, OrderItem
from .serializers import ProductSerializer, OrderSerializer, UserSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action in ['list', 'create', 'destroy', 'stats']:
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        sellers = User.objects.filter(is_seller=True)
        stats_data = []
        
        for seller in sellers:
            total_sales = OrderItem.objects.filter(
                product__seller=seller,
                order__status__in=['processing', 'shipped', 'delivered']
            ).aggregate(
                total=Sum(F('price') * F('quantity'), output_field=IntegerField())
            )['total'] or 0
            
            product_count = Product.objects.filter(seller=seller).count()
            
            stats_data.append({
                'id': seller.id,
                'username': seller.username,
                'total_sales': total_sales,
                'product_count': product_count,
            })
            
        return Response(stats_data)

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().order_by('-created_at')
    serializer_class = ProductSerializer
    parser_classes = (MultiPartParser, FormParser) # 👈 اضافه شد
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().order_by('-created_at')
    serializer_class = OrderSerializer
    permission_classes = [permissions.AllowAny]
