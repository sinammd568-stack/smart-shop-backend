from rest_framework import viewsets, permissions, status
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
    parser_classes = (MultiPartParser, FormParser)
    
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

    # 👈 منطق جدید برای ثبت سفارش همراه با آیتم‌ها
    def create(self, request, *args, **kwargs):
        data = request.data
        items_data = data.get('items', [])
        
        if not items_data:
            return Response({'error': 'سبد خرید خالی است'}, status=status.HTTP_400_BAD_REQUEST)

        # ساخت سفارش اصلی
        order = Order.objects.create(
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            phone=data.get('phone', ''),
            address=data.get('address', ''),
            total_price=data.get('total_price', 0),
            status='pending'
        )

        # ساخت آیتم‌های سفارش
        for item in items_data:
            OrderItem.objects.create(
                order=order,
                product_id=item.get('id'),
                price=item.get('price'),
                quantity=item.get('quantity')
            )

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
