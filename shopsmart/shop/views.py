from django.contrib.auth import authenticate
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter, OpenApiExample
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
                         OrderInfoCreateSerializer, EmailSerializer)
from .parameters import token_param, email_param, password_param, type_param, first_name_param, last_name_param, \
    city_param, phone_param, street_param, house_number_param, flat_number_param


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


@extend_schema(tags=['Register User'])
@extend_schema_view(
    post=extend_schema(
        summary='Регистрация магазина или пользователя',
        request=UserSerializer,
        parameters=[type_param, email_param, password_param, first_name_param, last_name_param],
        examples=[
            OpenApiExample(
                name='Register user',
                description='Регистрация магазина',
                value={
                    'type':'shop',
                    'email': 'example@example.com',
                    'password': '123456',
                    'first_name': 'John',
                    'last_name': 'Doe',
                },
            )
        ]
    ),
)
class RegisterUser(APIView):
    """
    Класс для регистрации нового магазина или пользователя.
    """
    serializer_class  = UserSerializer

    def post(self, request, *args, **kwargs):
        # Проверяем, что все необходимые поля присутствуют в запросе
        if {'email', 'password', 'first_name', 'last_name'}.issubset(request.data):
            try:
                # Проверяем корректность пароля с помощью функции validate_password
                validate_password(request.data['password'])
            except Exception as password_error:
                # Если пароль некорректен, возвращаем ошибку с соответствующим сообщением
                return JsonResponse({'Status': False, 'Errors': {'error': password_error}}, status=400)
            else:
                # Создаем сериализатор с данными из запроса
                serializer = UserSerializer(data=request.data)

                # Проверяем, валидны ли данные для создания пользователя
                if serializer.is_valid():
                    # Сохраняем пользователя и устанавливаем его пароль
                    user = serializer.save()
                    user.set_password(request.data['password'])
                    user.save()
                    # Возвращаем успешный ответ с данными пользователя
                    return JsonResponse({'Status': True, 'User': serializer.data})
                else:
                    # Если данные не валидны, возвращаем ошибки сериализации
                    return JsonResponse({'Status': False, 'Errors': {'error': serializer.errors}})

        # Если не указаны все необходимые аргументы, возвращаем ошибку
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


@extend_schema(tags=['Login User'])
@extend_schema_view(
    post=extend_schema(
        summary='Авторизация магазина или пользователя',
        request=UserSerializer,
        parameters=[email_param, password_param],
        examples=[
            OpenApiExample(
                name='User Login',
                description='Авторизация пользователя',
                value={
                    'email': 'john@example.com',
                    'password': 'password123'
                }
            ),
        ]
    ),
)
class LoginUserView(APIView):
    """
    Класс для авторизации магазина или пользователя
    """
    serializer_class = UserSerializer

    def post(self, request, *args, **kwargs):
        # Проверяем, что все необходимые поля присутствуют в запросе
        if {'email', 'password'}.issubset(request.data):
            # Авторизируем пользователя с помощью authenticate() и получаем его экземпляр
            user = authenticate(request, username=request.data['email'], password=request.data['password'])

            # Если пользователь авторизован, получаем его токен и возвращаем его
            if user is not None:
                token, _ = Token.objects.get_or_create(user=user)
                return JsonResponse({'Status': True, 'Token': token.key})

            return JsonResponse({'Status': False, 'Errors': 'Неправильный логин или пароль'}, status=404)

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})



@extend_schema(tags=['Confirm Email'])
@extend_schema_view(
    post=extend_schema(
        summary='Подтверждение email адреса пользователя',
        request=EmailSerializer,
        parameters=[email_param, token_param],
        examples=[
            OpenApiExample(
                name='Post example',
                description='Подтверждение email адреса',
                value={
                    "email": "user@example.com",
                    "token": "123456"
                }
            )
        ]
    ),
)
class ConfirmEmailView(APIView):
    """
    Класс для подтверждения email адреса пользователя
    """
    serializer_class = EmailSerializer


    def post(self, request, *args, **kwargs):
        # Проверяем, что все необходимые поля присутствуют в запросе
        if {'email', 'token'}.issubset(request.data):
            # Получаем токен по email и токену из запроса и проверяем их на совпадение
            token = EmailToken.objects.filter(email=request.data['email'], token=request.data['token']).first()

            # Если токен найден и активен, подтверждаем email и удаляем токен
            if token:
                token.user.is_active = True
                token.user.save()
                token.delete()
                return JsonResponse({'Status': True})
            return JsonResponse({'Status': False, 'Errors': 'Неправильный токен'})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


@extend_schema(tags=['User_information'])
@extend_schema_view(
    get=extend_schema(
        summary='Получение информации о пользователе',
    ),
    post=extend_schema(
        summary='Изменение информации о пользователе',
        request=UserInfoSerializer,
        parameters=[
            city_param,
            phone_param,
            street_param,
            house_number_param,
            flat_number_param,
        ],
    ),
)
class UserInfoView(APIView):
    """
    Класс для получения информации о пользователе
    """
    serializer_class = UserInfoSerializer

    def get(self, request, *args, **kwargs):
        #Проверяем, что пользователь авторизирован
        if request.user.is_authenticated:
            # Если пользователь авторизован, получаем данные о нем и возвращаем их
            serializer = UserInfoSerializer(request.user)
            return JsonResponse({'Status': True, 'User': serializer.data})

        return JsonResponse({'Status': False, 'Errors': 'Необходима авторизация'})


    def post(self, request, *args, **kwargs):
        # Проверяем, что пользователь авторизирован
        if request.user.is_authenticated:

            #Проверяем наличие пароля в запросе
            if 'password' in request.data:
                try:
                    # Проверяем корректность пароля с помощью validate_password
                    validate_password(request.data['password'])
                except Exception as password_error:
                    error_messages = []

                    for error_message in password_error:
                        error_messages.append(error_message)

                    return JsonResponse({'Status': False, 'Errors': error_messages})
                else:
                    request.user.set_password(request.data['password'])

            #Проверяем, валидны ли данные и сохраняем их
            serializer = UserInfoSerializer(request.user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return JsonResponse({'Status': True, 'User': serializer.data})
            else:
                return JsonResponse({'Status': False, 'Errors': serializer.errors})


@extend_schema(tags=['Category'])
@extend_schema_view(
    get=extend_schema(
        summary='Получение списка категорий товаров',
    ),
)
class CategoryView(ListAPIView):
    """
    Класс для получения списка категорий
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


@extend_schema(tags=['Shop'])
@extend_schema_view(
    get=extend_schema(
        summary='Получение списка магазинов',
    ),
)
class ShopView(ListAPIView):
    """
    Класс для получения списка магазинов
    """
    queryset = Shop.objects.filter(status=True)
    serializer_class = ShopSerializer


@extend_schema(tags=['Product'])
@extend_schema_view(
    get=extend_schema(
        summary='Получение информации о товаре',
    ),
)
class ProductInfoView(APIView):
    """
    Класс для получения информации о товарах.
    """
    pagination_class = InfoPagination  # Указываем класс пагинации для ответов
    serializer_class = ProductInfoSerializer

    def get(self, request, *args, **kwargs):
        # Создаем начальный запрос для фильтрации товаров,
        # учитывая только активные магазины (shop с status=True)
        query = Q(shop__status=True)

        # Получаем параметры фильтрации из запроса
        category_id = request.query_params.get('category_id')
        shop_id = request.query_params.get('shop_id')

        # Если указан идентификатор категории, добавляем условие к запросу
        if category_id:
            query &= Q(category_id=category_id)

        # Если указан идентификатор магазина, добавляем условие к запросу
        if shop_id:
            query &= Q(product__shop_id=shop_id)

        try:
            # Выполняем запрос к базе данных с учетом всех условий фильтрации,
            # выбираем связанные объекты для оптимизации запросов (select_related)
            # и подгружаем параметры продуктов (prefetch_related)
            queryset = ProductInfo.objects.filter(query).select_related(
                'product__category', 'shop').prefetch_related('product_parameters__parameter').distinct()

            # Инициализируем пагинатор и получаем страницу результатов
            paginator = self.pagination_class()
            page_query = paginator.paginate_queryset(queryset, request)

            # Сериализуем данные страницы с помощью сериализатора
            serializer = ProductInfoSerializer(page_query, many=True)

            # Возвращаем ответ с пагинированными данными
            return paginator.get_paginated_response(serializer.data)
        except Exception as e:
            return JsonResponse({'Status': False, 'Errors': str(e)})


@extend_schema(tags=['Basket',])
@extend_schema_view(
    get=extend_schema(
        summary='Получение списка товаров в корзине.',
    ),
    post=extend_schema(
        summary='Добавление товаров в корзину.',
        request=OrderSerializer,
    ),
    delete=extend_schema(
        summary='Удаление товаров из корзины'
    ),
    put=extend_schema(
        summary='Изменение количества товаров в корзине.',
        request=OrderSerializer,
    )
)
class BasketOfGoodsView(APIView):
    """
    Класс для добавления товаров в корзину.
    Этот класс обрабатывает GET и POST запросы для работы с корзиной пользователя.
    """
    pagination_class = InfoPagination  # Указываем класс пагинации для ответов
    def get_serializer_class(self):
        if self.request.method in ['POST', 'PUT']:
            return OrderInfoSerializer
        return OrderSerializer

    def get(self, request, *args, **kwargs):
        # Проверяем, авторизован ли пользователь
        if request.user.is_authenticated:
            try:
                # Получаем корзину пользователя с учетом связанных объектов и суммируем стоимость товаров
                basket = Order.objects.filter(user_id=request.user.id, status='basket').prefetch_related(
                    'order_info__product_info__product__category',
                    'order_info__product_info__product_parameters__parameter').annotate(
                    total_sum=Sum(F('order_info__product_info__product__price') * F('order_info__quantity'))).distinct()

                # Инициализируем пагинатор и получаем страницу результатов
                paginator = self.pagination_class()
                page_query = paginator.paginate_queryset(basket, request)

                # Сериализуем данные страницы с помощью сериализатора
                serializer = OrderSerializer(page_query, many=True)

                # Возвращаем ответ с пагинированными данными
                return paginator.get_paginated_response(serializer.data)
            except Exception as e:
                # В случае возникновения ошибки возвращаем сообщение об ошибке
                return JsonResponse({'Status': False, 'Errors': str(e)})
        else:
            # Если пользователь не авторизован, возвращаем сообщение об ошибке
            return JsonResponse({'Status': False, 'Errors': 'Необходима авторизация'})

    def post(self, request, *args, **kwargs):
        # Проверяем, авторизован ли пользователь
        if request.user.is_authenticated:
            items_list = request.data.get('items')  # Получаем список товаров из запроса
            if items_list:
                try:
                    # Загружаем список товаров из JSON
                    item_dict = load_json(items_list)
                except ValueError:
                    return JsonResponse({'Status': False, 'Errors': 'Ошибка при загрузке товаров'})
                else:
                    # Получаем или создаем корзину для пользователя
                    basket, _ = Order.objects.get_or_create(user_id=request.user.id, status='basket')
                    obj_create = 0  # Счетчик успешно созданных объектов

                    for order_item in item_dict:
                        order_item.update({'order': basket})  # Привязываем товар к корзине
                        serializer = OrderInfoSerializer(data=order_item)  # Создаем сериализатор для товара

                        if serializer.is_valid():
                            try:
                                # Сохраняем товар в корзину
                                serializer.save()
                            except IntegrityError as e:
                                return JsonResponse({'Status': False, 'Errors': str(e)})
                            else:
                                obj_create += 1  # Увеличиваем счетчик успешно созданных объектов

                        else:
                            return JsonResponse({'Status': False, 'Errors': serializer.errors})

                    # Возвращаем успешный ответ с количеством созданных объектов
                    return JsonResponse({'Status': True, 'Создано объектов': obj_create})

            return JsonResponse({'Status': False, 'Errors': 'Ошибка при добавлении товаров в корзину'})
        else:
            return JsonResponse({'Status': False, 'Errors': 'Необходима авторизация'})

    def delete(self, request, *args, **kwargs):
        # Проверяем, авторизован ли пользователь
        if request.user.is_authenticated:
            #Получаем список товаров из запроса
            item_list = request.data.get('items')

            if item_list:
                try:
                    # Загружаем список товаров из JSON
                    item_dict = load_json(item_list)
                except ValueError:
                    return JsonResponse({'Status': False, 'Errors': 'Ошибка при загрузке товаров'})
                else:
                    # Получаем корзину пользователя с учетом связанных объектов и суммируем стоимость товаров
                    basket = Order.objects.filter(user_id=request.user.id, status='basket')
                    obj_delete = 0
                    for order_item in item_dict:
                        try:
                            OrderInfo.objects.filter(order=basket, product_info_id=order_item['product_info_id']).delete()
                        except ObjectDoesNotExist:
                            return JsonResponse({'Status': False, 'Errors': 'Товар не найден в корзине'})
                        else:
                            obj_delete += 1

                return JsonResponse({'Status': True, 'Удалено объектов': obj_delete})

            return JsonResponse({'Status': False, 'Errors': 'Ошибка при удалении товаров из корзины'})

        return JsonResponse({'Status': False, 'Errors': 'Необходима авторизация'})


    def put(self, request, *args, **kwargs):
        # Проверяем, авторизован ли пользователь
        if request.user.is_authenticated:
            # Получаем список товаров из запроса
            item_list = request.data.get('items')

            if item_list:
                try:
                    # Загружаем список товаров из JSON
                    item_dict = load_json(item_list)
                except ValueError:
                    return JsonResponse({'Status': False, 'Errors': 'Ошибка при загрузке товаров'})
                else:
                    # Получаем корзину пользователя с учетом связанных объектов и суммируем стоимость товаров
                    basket = Order.objects.filter(user_id=request.user.id, status='basket')
                    obj_update = 0
                    for order_item in item_dict:
                        try:
                            order_info = OrderInfo.objects.filter(order=basket, product_info_id=order_item['product_info_id']).first()
                            order_info.quantity = order_item['quantity']
                            order_info.save()
                        except ObjectDoesNotExist:
                            return JsonResponse({'Status': False, 'Errors': 'Товар не найден в корзине'})
                        else:
                            obj_update += 1

                    return JsonResponse({'Status': True, 'Обновлено объектов': obj_update})

            return JsonResponse({'Status': False, 'Errors': 'Ошибка при изменении количества товаров в корзине'})

        return JsonResponse({'Status': False, 'Errors': 'Необходима авторизация'})


@extend_schema(tags=['Contact'])
@extend_schema_view(
    post=extend_schema(
        summary='Создание пользовательской информации',
        request=UserInfoSerializer,
    ),
    put=extend_schema(
        summary='Изменение пользовательской информации',
        request=UserInfoSerializer,
    ),
    get=extend_schema(
        summary='Получение пользовательской информации',
    ),
    delete=extend_schema(
        summary='Удаление пользовательской информации',
    )

)
class UserContactView(APIView):
    """
    Класс для добавления/изменения пользовательской информации
    """
    serializer_class = UserInfoSerializer


    def get(self, request, *args, **kwargs):
        #Ппроверяем, авторизирован ли пользователь
        if request.user.is_authenticated:
            try:
                #Если пользователь авторизирован, получаем данные и отправляем их
                serializer = UserInfoSerializer(user_info=request.user.get('user_info'))
            except ObjectDoesNotExist:
                return JsonResponse({'Status': False, 'Errors': 'Информация о пользователе не найдена'})
            else:
                return JsonResponse({'Status': True, 'User': serializer.data})

        return JsonResponse({'Status': False, 'Errors': 'Необходима авторизация'})

    def post(self, request, *args, **kwargs):
        # Проверяем, авторизован ли пользователь
        if request.user.is_authenticated:

            #Проверяем наличие обязательных полей
            if {'city', 'street', 'phone'}.issubset(request.data):
                #Если все поля есть, меняем данные и сохраняем
                request.data._mutable = True
                request.data.update({'user': request.user.id})
                serializer = UserInfoSerializer(data=request.data)

                #Проверяем банные на валидность и сохраняем
                if serializer.is_valid():
                    serializer.save()
                    return JsonResponse({'Status': True, 'User': serializer.data})
                else:
                    return JsonResponse({'Status': False, 'Errors': serializer.errors})

            return JsonResponse({'Status': False, 'Errors': 'Недостаточно данных для сохранения информации о пользователе'})

        return JsonResponse({'Status': False, 'Errors': 'Необходима авторизация'})

    def delete(self, request, *args, **kwargs):
        # Проверяем, авторизован ли пользователь
        if request.user.is_authenticated:
            # Получаем строку с идентификаторами товаров из запроса
            item_string = request.data.get('items')
            if item_string:
                # Разделяем строку по запятой и создаем список идентификаторов
                item_list = item_string.split(',')
                query = Q()  # Инициализируем пустой запрос для фильтрации объектов
                objects_deleted = False  # Флаг для отслеживания удаления объектов

                # Проходим по каждому идентификатору в списке
                for item_id in item_list:
                    if item_id.isdigit():  # Проверяем, является ли идентификатор числом
                        # Добавляем условие в запрос для фильтрации по пользователю и идентификатору
                        query |= Q(user_id=request.user.id, id=item_id)
                        objects_deleted = True  # Устанавливаем флаг, что есть объекты для удаления

                # Если есть объекты для удаления
                if objects_deleted:
                    # Удаляем объекты и получаем количество удаленных записей
                    delete_count = UserInfo.objects.filter(query).delete()[0]
                    return JsonResponse({'Status': True, 'Удалено объектов': delete_count})

            return JsonResponse({'Status': False, 'Errors': 'Ошибка при удалении информации о пользователе'})

        return JsonResponse({'Status': False, 'Errors': 'Необходима авторизация'})

    def put(self, request, *args, **kwargs):
        # Проверяем, авторизован ли пользователь
        if request.user.is_authenticated:
            # Проверяем, присутствует ли идентификатор в данных запроса и является ли он числом
            if 'id' in request.data and request.data['id'].isdigit():
                # Получаем объект UserInfo, связанный с текущим пользователем и указанным идентификатором
                user_info = UserInfo.objects.filter(user=request.user.id, id=request.data['id']).first()
                if user_info:  # Если объект найден
                    # Создаем сериализатор с данными для обновления (частичное обновление)
                    serializer = UserInfoSerializer(user_info, data=request.data, partial=True)
                    if serializer.is_valid():  # Проверяем валидность данных
                        serializer.save()  # Сохраняем обновленные данные
                        return JsonResponse({'Status': True,
                                             'User': serializer.data})  # Возвращаем успешный ответ с данными пользователя
                    else:
                        # Если данные не валидны, возвращаем ошибки сериализации
                        return JsonResponse({'Status': False, 'Errors': serializer.errors})

                return JsonResponse({'Status': False, 'Errors': 'Информация о пользователе не найдена'})

            return JsonResponse(
                {'Status': False, 'Errors': 'Недостаточно данных для сохранения информации о пользователе'})

        return JsonResponse({'Status': False, 'Errors': 'Необходима авторизация'})


@extend_schema(tags=['Order'])
@extend_schema_view(
    get=extend_schema(
        summary='Получение заказов пользователя',
        request=OrderSerializer(many=True),
    ),
    post=extend_schema(
        summary='Создание заказа',
        request=OrderSerializer,
    ),
)
class OrderView(APIView):
    """
    Класс для получения и размещения заказов пользователя
    """
    serializer_class = OrderSerializer

    def get(self, request, *args, **kwargs):
        # Проверяем, авторизован ли пользователь
        if request.user.is_authenticated:
            try:
                # Если пользователь авторизирован, получаем данные заказов и отправляем их
                order = Order.objects.filter(user_id=request.user.id).prefetch_related(
                    'order_info__product_info__product__category',
                    'order_info__product_info__product_parameters__parameter').select_related('user_info').annotate(
                    total_price=Sum(F('order_info__product_info__price') * F('order_info__quantity'))).distinct()
            except ObjectDoesNotExist as e:
                return JsonResponse({'Status': False, 'Errors': str(e)})
            else:
                serializer = OrderSerializer(order, many=True)
                return JsonResponse({'Status': True, 'Orders': serializer.data})

        return JsonResponse({'Status': False, 'Errors': 'Необходима авторизация'})


    def post(self, request, *args, **kwargs):
        # Проверяем, авторизован ли пользователь
        if request.user.is_authenticated:
            # Проверяем наличие обязательных полей
            if {'id', 'user_info'}.issubset(request.data):
                # Получаем объект UserInfo, связанный с текущим пользователем и указанным идентификатором
                if request.data['id'].isdigit():
                    try:
                        #Находим заказ по id  и меняем его статус
                        order = Order.objects.filter(user_id=request.user.id, id=request.data['id']).update(
                            contact_id=request.data['contact'], status='new')
                    except IntegrityError as e:
                        return JsonResponse({'Status': False, 'Errors': str(e)})
                    else:
                        if order:
                            #Отправляем ссылку для подтверждения на почту
                            new_order.send(sender=self.__class__, user_id=request.user.id)
                            return JsonResponse({'Status': True, 'Order': {'id': request.data['id']}})
                        else:
                            return JsonResponse({'Status': False, 'Errors': 'Заказ не найден'})

                return JsonResponse({'Status': False, 'Errors': 'Недостаточно данных для создания заказа'})

            return JsonResponse({'Status': False, 'Errors': 'Недостаточно данных для создания заказа'})

        return JsonResponse({'Status': False, 'Errors': 'Необходима авторизация'})



# class UpdateShopStatusView(APIView):
#     """
#     Класс для изменения статуса магазина
#     """
#     def put(self, request, *args, **kwargs):
#         if request.user.is_authenticated:
#             if request.user.type == 'shop':

