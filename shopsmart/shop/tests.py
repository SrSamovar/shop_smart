from http.client import responses
from itertools import product

from celery.bin.control import status
from rest_framework.test import force_authenticate, APIRequestFactory, APIClient, APITestCase
from.models import User, Shop, Category, Product, ProductInfo, Parameter, Order, EmailToken, OrderInfo, UserInfo

factory = APIRequestFactory()


class UserTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()

    def test_create_user(self):
        response = self.client.post('/api/v1/user/register',
                                    {
                                        'type': 'user',
                                        'email': 'testuser@example.com',
                                        'password': '123456',
                                        'first_name': 'Test',
                                        'last_name': 'User',
                                    })
        self.assertEqual(response.status_code, 200)


    def test_user_login(self):
        user = User.objects.create_user(email='testuser@example.com', password='123456')
        response = self.client.post('/api/v1/user/login', {'email': 'testuser@example.com', 'password': '123456'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('token', response.data)


class UserInfoTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='testuser@example.com', password='123456')
        self.client.force_authenticate(user=self.user)

    def test_update_user_info(self):
        data = {
            'city': 'New York',
            'phone': '1234567890',
            'street': 'Main Street',
            'house_number': '10',
            'flat_number': '1A',
        }
        response = self.client.patch('/api/v1/user/info', data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('id', response.data)
        self.assertEqual(response.data['city'], 'New York')

    def test_get_user_info(self):
        response = self.client.get('/api/v1/user/info')
        self.assertEqual(response.status_code, 200)
        self.assertIn('id', response.data)

    def test_invalid_data(self):
        new_data = {
            'city': '',
            'phone': '1234567890',
            'street': 'Main Street',
            'house_number': '10',
            'flat_number': '1A',
        }
        response = self.client.post('/api/v1/user/info', new_data)
        self.assertEqual(response.status_code, 400)
        self.assertIn('city', response.data['errors'])

    def test_delete_info(self):
        response = self.client.delete('/api/v1/user/info')
        self.assertEqual(response.status_code, 200)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['message'], 'Информация о пользователе успешно удалена')


class CategoryTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='testuser@example.com', password='123456')
        self.client.force_authenticate(user=self.user)

        self.categories = [
            Category.objects.create(name='Electronics'),
            Category.objects.create(name='Clothes'),
            Category.objects.create(name='Books'),
        ]

    def test_get_categories(self):
        response = self.client.get('/api/v1/categories')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 3)
        self.assertIn('id', response.data[0])
        self.assertIn('name', response.data[0])

        for category in response.data:
            self.assertIn(category['name'], [c.name for c in self.categories])


class ShopTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='testuser@example.com', password='123456')
        self.client.force_authenticate(user=self.user)

        self.shops = [
            Shop.objects.create(name='Test Shop 1'),
            Shop.objects.create(name='Test Shop 2'),
            Shop.objects.create(name='Test Shop 3'),
        ]

    def test_get_shops(self):
        response = self.client.get('/api/v1/shops')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 3)
        self.assertIn('id', response.data[0])
        self.assertIn('name', response.data[0])

        for shop in response.data:
            self.assertIn(shop['name'], [s.name for s in self.shops])


class BasketOfGoodsTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='testuser@example.com', password='123456')
        self.client.force_authenticate(user=self.user)
        self.product = Product.objects.create(name='Test Product')
        self.product_info = ProductInfo.objects.create(product=self.product, price=100)

    def test_add_to_basket(self):
        data = {
            'product_info_id': self.product_info.id,
            'quantity': 2,
        }
        response = self.client.post('/api/v1/basket', data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('id', response.data)
        self.assertEqual(response.data['product_info_id'], self.product_info.id)
        self.assertEqual(response.data['quantity'], 2)

    def test_get_basket(self):
        self.test_add_to_basket()

        response = self.client.get('/api/v1/basket')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertIn('id', response.data[0])

    def test_update_basket(self):
        self.test_add_to_basket()

        data = {
            'order_info_id': 1,
            'quantity': 3,
        }
        response = self.client.put('/api/v1/basket', data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('id', response.data)
        self.assertEqual(response.data['quantity'], 3)

    def test_delete_basket(self):
        self.test_add_to_basket()

        response = self.client.delete('/api/v1/basket/1', {'order_info_id': 1})
        self.assertEqual(response.status_code, 200)


class ProductInfoViewTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='testuser@example.com', password='123456')
        self.client.force_authenticate(user=self.user)
        self.shop =Shop.objects.create(name='Test Shop', status=True)
        self.category = Category.objects.create(name='Test Category')
        self.product = Product.objects.create(name='Test Product', shop=self.shop, category=self.category)
        self.product_info = ProductInfo.objects.create(product=self.product, price=100, quantity=2)

    def test_get_product_info(self):
        response = self.client.get('api/v1/product/info')
        self.assertEqual(response.status_code, 200)
        self.assertIn('id', response.data[0])
