from rest_framework import serializers
from .models import Product, Order, OrderItem, User

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'is_seller', 'is_staff', 'password')

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user

class ProductSerializer(serializers.ModelSerializer):
    seller_name = serializers.ReadOnlyField(source='seller.username')
    
    class Meta:
        model = Product
        # 👈 فیلدها رو دقیق مشخص کردیم تا seller از سمت فرانت‌اند اجباری نباشه
        fields = ['id', 'name', 'description', 'price', 'old_price', 'category', 'image', 'tag', 'rating', 'created_at', 'seller', 'seller_name']
        read_only_fields = ['seller', 'seller_name', 'rating', 'created_at'] # 👈 اینا فقط خواندنی هستن

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name')
    
    class Meta:
        model = OrderItem
        fields = ('id', 'product', 'product_name', 'price', 'quantity')

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = ('id', 'first_name', 'last_name', 'phone', 'address', 'total_price', 'status', 'created_at', 'items')
