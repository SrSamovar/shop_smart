from django.contrib.auth import authenticate
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import URLValidator
from django.db import IntegrityError
from .signals import new_order
from django.db.models import Q, F, Sum
from django.http import JsonResponse
from rest_framework.authtoken.models import Token
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from yaml import load as load_yaml, Loader
from ujson import load as load_json
from requests import get
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from django.contrib.auth.password_validation import validate_password
from .models import ProductInfo, Shop, Category, Product, ProductParameter, Parameter, Order, EmailToken, \
    OrderInfo, UserInfo
from .serializers import (UserSerializer, ShopSerializer, CategorySerializer, ProductSerializer, ProductInfoSerializer,
                         ProductParameterSerializer, OrderSerializer, OrderInfoSerializer, UserInfoSerializer,
                         OrderInfoCreateSerializer)


class InfoPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class PartnerUpdate(APIView):
    """
    Класс для обновления прайса от поставщика
    """
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Только для магазинов'}, status=403)

        url = request.data.get('url')
        if url:
            validate_url = URLValidator()
            try:
                validate_url(url)
            except ValidationError as e:
                return JsonResponse({'Status': False, 'Error': str(e)})
            else:
                stream = get(url).content

                data = load_yaml(stream, Loader=Loader)

                shop, _ = Shop.objects.get_or_create(name=data['shop'], user_id=request.user.id)
                for category in data['categories']:
                    category_object, _ = Category.objects.get_or_create(id=category['id'], name=category['name'])
                    category_object.shops.add(shop.id)
                    category_object.save()
                ProductInfo.objects.filter(shop_id=shop.id).delete()
                for item in data['goods']:
                    product, _ = Product.objects.get_or_create(name=item['name'], category_id=item['category'])

                    product_info = ProductInfo.objects.create(product_id=product.id,
                                                              external_id=item['id'],
                                                              model=item['model'],
                                                              price=item['price'],
                                                              price_rrc=item['price_rrc'],
                                                              quantity=item['quantity'],
                                                              shop_id=shop.id)
                    for name, value in item['parameters'].items():
                        parameter_object, _ = Parameter.objects.get_or_create(name=name)
                        ProductParameter.objects.create(product_info_id=product_info.id,
                                                        parameter_id=parameter_object.id,
                                                        value=value)

                return JsonResponse({'Status': True})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class RegisterUser(APIView):
    """
    Класс для регистрации нового магазина или пользователя
    """
    def post(self, request, *args, **kwargs):
        if request['status'] == 'shop':
            if {'email', 'password', 'first_name', 'last_name', 'company', 'position'}.issubset(request.data):

                try:
                    validate_password(request.data['password'])
                except Exception as password_error:
                    error_messages = []

                    for item in password_error:
                        error_messages.append(item)

                    return JsonResponse({'Status': False, 'Errors': error_messages}, status=400)
                else:
                    serializer = UserSerializer(data=request.data)

                    if serializer.is_valid():
                        user = serializer.save()
                        user.set_password(request.data['password'])
                        user.save()
                        return JsonResponse({'Status': True, 'User': serializer.data})
                    else:
                        return JsonResponse({'Status': False, 'Errors': serializer.errors}, status=400)

        if request['status'] == 'buyer':

            if {'email', 'password', 'first_name', 'last_name'}.issubset(request.data):
                try:
                    validate_password(request.data['password'])
                except Exception as password_error:
                    error_messages = []

                    for item in password_error:
                        error_messages.append(item)

                    return JsonResponse({'Status': False, 'Errors': error_messages}, status=400)
                else:
                    serializer = UserSerializer(data=request.data)

                    if serializer.is_valid():
                        user = serializer.save()
                        user.set_password(request.data['password'])
                        user.save()
                        return JsonResponse({'Status': True, 'User': serializer.data})
                    else:
                        return JsonResponse({'Status': False, 'Errors': serializer.errors}, status=400)

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class LoginUserView(APIView):
    """
    Класс для авторизации магазина или пользователя
    """
    def post(self, request, *args, **kwargs):

        if {'email', 'password'}.issubset(request.data):
            user = authenticate(email=request.data['email'], password=request.data['password'])

            if user is not None:
                token = Token.objects.get_or_create(user=user)
                return JsonResponse({'Status': True, 'Token': token[0].key})

            return JsonResponse({'Status': False, 'Errors': 'Неправильный логин или пароль'})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class ConfirmEmailView(APIView):
    """
    Класс для подтверждения email адреса пользователя
    """
    def post(self, request, *args, **kwargs):
        if {'email', 'token'}.issubset(request.data):
            token = EmailToken.objects.filter(email=request.data['email'], token=request.data['token']).first()

            if token:
                token.user.is_active = True
                token.user.save()
                token.delete()
                return JsonResponse({'Status': True})
            return JsonResponse({'Status': False, 'Errors': 'Неправильный токен'})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})



class UserInfoView(APIView):
    """
    Класс для получения информации о пользователе
    """

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            serializer = UserInfoSerializer(request.user)
            return JsonResponse({'Status': True, 'User': serializer.data})

        return JsonResponse({'Status': False, 'Errors': 'Необходима авторизация'})


    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:

            if 'password' in request.data:
                try:
                    validate_password(request.data['password'])
                except Exception as password_error:
                    error_messages = []

                    for item in password_error:
                        error_messages.append(item)

                    return JsonResponse({'Status': False, 'Errors': error_messages}, status=400)
                else:
                    request.user.set_password(request.data['password'])

            serializer = UserInfoSerializer(request.user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return JsonResponse({'Status': True, 'User': serializer.data})
            else:
                return JsonResponse({'Status': False, 'Errors': serializer.errors}, status=400)


class CategoryView(ListAPIView):
    """
    Класс для получения списка категорий
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ShopView(ListAPIView):
    """
    Класс для получения списка магазинов
    """
    queryset = Shop.objects.filter(status=True)
    serializer_class = ShopSerializer


class ProductInfoView(APIView):
    """
    Класс для получения информации о товарах
    """
    pagination_class = InfoPagination


    def get(self, request, *args, **kwargs):
        query = Q(shop__status=True)

        category_id = request.query_params.get('category_id')
        shop_id = request.query_params.get('shop_id')

        if category_id:
            query &= Q(category_id=category_id)

        if shop_id:
            query &= Q(product__shop_id=shop_id)

        try:
            queryset = ProductInfo.objects.filter(query).select_related(
                'product__category', 'shop').prefetch_related('product_parameters__parameter').distinct()

            paginator = self.pagination_class()
            page_query = paginator.paginate_queryset(queryset, request)

            serializer = ProductInfoSerializer(page_query, many=True)
            return paginator.get_paginated_response(serializer.data)
        except Exception as e:
            return JsonResponse({'Status': False, 'Errors': str(e)}, status=500)


class BasketOfGoodsView(APIView):
    """
    Класс для добавления товаров в корзину
    """
    pagination_class = InfoPagination
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            try:
                basket = Order.objects.filter(user_id=request.user.id,status='basket').prefect_related(
                    'order_info__product_info__product__category',
                    'order_info__product_info__product_parameters__parameter').annotate(
                    total_sum=Sum(F('order_info__product_info__product__price') * F('order_info__quantity'))).distinct()

                paginator = self.pagination_class()
                page_query = paginator.paginate_queryset(basket, request)

                serializer = OrderSerializer(page_query, many=True)
                return paginator.get_paginated_response(serializer.data)
            except Exception as e:
                return  JsonResponse({'Status': False, 'Errors': str(e)}, status=500)
        else:
            return JsonResponse({'Status': False, 'Errors': 'Необходима авторизация'})


    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            items_list = request.data.get('items')
            if items_list:
                try:
                    item_dict = load_json(items_list)
                except ValueError:
                    return JsonResponse({'Status': False, 'Errors': 'Ошибка при загрузке товаров'}, status=400)
                else:
                    basket, _ = Order.objects.get_or_create(user_id=request.user.id, status='basket')
                    obj_create = 0
                    for order_item in item_dict:
                        order_item.update({'order': basket})
                        serializer = OrderInfoSerializer(data=order_item)
                        if serializer.is_valid():
                            try:
                                serializer.save()
                            except IntegrityError as e:
                                return JsonResponse({'Status': False, 'Errors': str(e)}, status=400)
                            else:
                                obj_create += 1

                        else:
                            return JsonResponse({'Status': False, 'Errors': serializer.errors}, status=400)

                    return JsonResponse({'Status': True, 'Создано объектов': obj_create})

            return JsonResponse({'Status': False, 'Errors': 'Ошибка при добавлении товаров в корзину'}, status=500)
        else:
            return JsonResponse({'Status': False, 'Errors': 'Необходима авторизация'})



    def delete(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            item_list = request.data.get('items')

            if item_list:
                try:
                    item_dict = load_json(item_list)
                except ValueError:
                    return JsonResponse({'Status': False, 'Errors': 'Ошибка при загрузке товаров'}, status=400)
                else:
                    basket = Order.objects.filter(user_id=request.user.id, status='basket')
                    obj_delete = 0
                    for order_item in item_dict:
                        try:
                            OrderInfo.objects.filter(order=basket, product_info_id=order_item['product_info_id']).delete()
                        except ObjectDoesNotExist:
                            return JsonResponse({'Status': False, 'Errors': 'Товар не найден в корзине'}, status=404)
                        else:
                            obj_delete += 1

                return JsonResponse({'Status': True, 'Удалено объектов': obj_delete})

            return JsonResponse({'Status': False, 'Errors': 'Ошибка при удалении товаров из корзины'}, status=500)

        return JsonResponse({'Status': False, 'Errors': 'Необходима авторизация'})


    def put(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            item_list = request.data.get('items')

            if item_list:
                try:
                    item_dict = load_json(item_list)
                except ValueError:
                    return JsonResponse({'Status': False, 'Errors': 'Ошибка при загрузке товаров'}, status=400)
                else:
                    basket = Order.objects.filter(user_id=request.user.id, status='basket')
                    obj_update = 0
                    for order_item in item_dict:
                        try:
                            order_info = OrderInfo.objects.filter(order=basket, product_info_id=order_item['product_info_id']).first()
                            order_info.quantity = order_item['quantity']
                            order_info.save()
                        except ObjectDoesNotExist:
                            return JsonResponse({'Status': False, 'Errors': 'Товар не найден в корзине'}, status=404)
                        else:
                            obj_update += 1

                    return JsonResponse({'Status': True, 'Обновлено объектов': obj_update})

            return JsonResponse({'Status': False, 'Errors': 'Ошибка при изменении количества товаров в корзине'}, status=500)

        return JsonResponse({'Status': False, 'Errors': 'Необходима авторизация'})


class UserContactView(APIView):
    """
    Класс для добавления/изменения пользовательской информации
    """
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            try:
                serializer = UserInfoSerializer(user_info=request.user.get('user_info'))
            except ObjectDoesNotExist:
                return JsonResponse({'Status': False, 'Errors': 'Информация о пользователе не найдена'}, status=404)
            else:
                return JsonResponse({'Status': True, 'User': serializer.data})

        return JsonResponse({'Status': False, 'Errors': 'Необходима авторизация'})

    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:

            if {'city', 'street', 'phone'}.issubset(request.data):
                request.data._mutable = True
                request.data.update({'user': request.user.id})
                serializer = UserInfoSerializer(data=request.data)

                if serializer.is_valid():
                    serializer.save()
                    return JsonResponse({'Status': True, 'User': serializer.data})
                else:
                    return JsonResponse({'Status': False, 'Errors': serializer.errors}, status=400)

            return JsonResponse({'Status': False, 'Errors': 'Недостаточно данных для сохранения информации о пользователе'}, status=400)

        return JsonResponse({'Status': False, 'Errors': 'Необходима авторизация'})


    def delete(self, request, *args, **kwargs):

        if request.user.is_authenticated:
            item_string = request.data.get('items')
            if item_string:
                item_list = item_string.split(',')
                query = Q()
                objects_deleted = False

                for item_id in item_list:
                    if item_id.isdigit():
                        query |= Q(user_id=request.user.id, id=item_id)
                        objects_deleted = True

                if objects_deleted:
                    delete_count = UserInfo.objects.filter(query).delete()[0]
                    return JsonResponse({'Status': True, 'Удалено объектов': delete_count})

            return JsonResponse({'Status': False, 'Errors': 'Ошибка при удалении информации о пользователе'}, status=500)

        return JsonResponse({'Status': False, 'Errors': 'Необходима авторизация'})


    def put(self, request, *args, **kwargs):

        if request.user.is_authenticated:
            if 'id' in request.data and request.data['id'].isdigit():
                user_info = UserInfo.objects.filter(user=request.user.id, id=request.data['id']).first()
                if user_info:
                    serializer = UserInfoSerializer(user_info, data=request.data, partial=True)
                    if serializer.is_valid():
                        serializer.save()
                        return JsonResponse({'Status': True, 'User': serializer.data})
                    else:
                        return JsonResponse({'Status': False, 'Errors': serializer.errors}, status=400)

                return JsonResponse({'Status': False, 'Errors': 'Информация о пользователе не найдена'}, status=404)

            return JsonResponse({'Status': False, 'Errors': 'Недостаточно данных для сохранения информации о пользователе'}, status=400)

        return JsonResponse({'Status': False, 'Errors': 'Необходима авторизация'})


class OrderView(APIView):
    """
    Класс для получения и размещения заказов пользователя
    """

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            try:
                order = Order.objects.filter(user_id=request.user.id).prefetch_related(
                    'order_info__product_info__product__category',
                    'order_info__product_info__product_parameters__parameter').select_related('user_info').annotate(
                    total_price=Sum(F('order_info__product_info__price') * F('order_info__quantity'))).distinct()
            except ObjectDoesNotExist as e:
                return JsonResponse({'Status': False, 'Errors': str(e)}, status=404)
            else:
                serializer = OrderSerializer(order, many=True)
                return JsonResponse({'Status': True, 'Orders': serializer.data})

        return JsonResponse({'Status': False, 'Errors': 'Необходима авторизация'})


    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if {'id', 'user_info'}.issubset(request.data):
                if request.data['id'].isdigit():
                    try:
                        order = Order.objects.filter(user_id=request.user.id, id=request.data['id']).update(
                            contact_id=request.data['contact'], status='new')
                    except IntegrityError as e:
                        return JsonResponse({'Status': False, 'Errors': str(e)}, status=400)
                    else:
                        if order:
                            new_order.send(sender=self.__class__, user_id=request.user.id)
                            return JsonResponse({'Status': True, 'Order': {'id': request.data['id']}})
                        else:
                            return JsonResponse({'Status': False, 'Errors': 'Заказ не найден'}, status=404)

                return JsonResponse({'Status': False, 'Errors': 'Недостаточно данных для создания заказа'}, status=400)

            return JsonResponse({'Status': False, 'Errors': 'Недостаточно данных для создания заказа'}, status=400)

        return JsonResponse({'Status': False, 'Errors': 'Необходима авторизация'})



# class UpdateShopStatusView(APIView):
#     """
#     Класс для изменения статуса магазина
#     """
#     def put(self, request, *args, **kwargs):
#         if request.user.is_authenticated:
#             if request.user.type == 'shop':

