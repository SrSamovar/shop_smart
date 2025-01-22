from django.core.validators import URLValidator
from django.http import JsonResponse
from django.shortcuts import render
from yaml import load, Loader
from requests import get
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from shopsmart.shop.models import ProductInfo, Shop, Category, Product, ProductParameter, Parameter, User


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

                data = load(stream, Loader=Loader)

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
        if request.data.get('type') == 'shop':
            if {'first_name', 'last_name', 'email', 'password', 'company', 'position'}.issubset(request.data):
                user = User.objects.create_user(email=request.data.get('email'),
                                            password=request.data.get('password'),
                                            type='shop',
                                            first_name=request.data.get('first_name'),
                                            last_name=request.data.get('last_name'),
                                            company=request.data.get('company'),
                                            position=request.data.get('position'))
                return JsonResponse({'Status': True})
        elif request.data.get('type') == 'user':
            if {'first_name', 'last_name', 'email', 'password'}.issubset(request.data):
                user = User.objects.create_user(email=request.data.get('email'),
                                            password=request.data.get('password'),
                                            type='buyer',
                                            first_name=request.data.get('first_name'),
                                            last_name=request.data.get('last_name'))
                return JsonResponse({'Status': True})
        else:
            return JsonResponse({'Status': False, 'Error': 'Не указано правильное значение поля type'})

