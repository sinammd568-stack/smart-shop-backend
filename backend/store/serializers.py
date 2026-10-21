from rest_framework import serializers
from .models import Product, Order, OrderItem, User

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False) # 👈 برای ساخت کاربر جدید

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
    seller_name = serializers.ReadOnlyField(source='seller.username') # 👈 اسم فروشنده رو نشون بده
    
    class Meta:
        model = Product
        fields = '__all__'
