from rest_framework import serializers
from .models import User, Shop, Category, Product, ProductInfo, ProductParameter, OrderInfo, Order, UserInfo


class UserInfoSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserInfo
        fields = ('id', 'user', 'address', 'phone', 'city', 'country')
        read_only_fields = ('id', 'user')


class UserSerializer(serializers.ModelSerializer):
    user_info = UserInfoSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'type', 'user_info', 'company','position')
        read_only_fields = ('id', 'email')



class ShopSerializer(serializers.ModelSerializer):

    class Meta:
        model = Shop
        fields = ('id', 'name', 'url','status')
        read_only_fields = ('id', 'name')


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ('id', 'name')


class ProductSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()

    class Meta:
        model = Product
        fields = ('id', 'name', 'category', 'price')


class ProductParameterSerializer(serializers.ModelSerializer):
    parameter = serializers.StringRelatedField()

    class Meta:
        model = ProductParameter
        fields = ('id', 'parameter', 'value')


class ProductInfoSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_parameters = ProductParameterSerializer(many=True, read_only=True)

    class Meta:
        model = ProductInfo
        fields = ('id', 'product', 'model', 'price', 'price_rrc', 'quantity','shop', 'product_parameters')


class OrderInfoSerializer(serializers.ModelSerializer):

    class Meta:
        model = OrderInfo
        fields = ('id', 'order', 'product_info', 'quantity', 'price')
        read_only_fields = ('id', 'order')


class OrderInfoCreateSerializer(serializers.ModelSerializer):
    product_info = ProductInfoSerializer(read_only=True)


class OrderSerializer(serializers.ModelSerializer):
    order_info = OrderInfoSerializer(many=True, read_only=True)

    total_sum = serializers.IntegerField()
    user_info = UserInfoSerializer(read_only=True)

    class Meta:
        model = Order
        fields = ('id', 'user_info', 'created_at','status', 'order_info', 'total_sum')
        read_only_fields = ('id', 'created_at','status')
