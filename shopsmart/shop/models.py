from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.utils.translation import gettext_lazy as _
from django.db import models
from django.contrib.auth.models import AbstractUser
from django_rest_passwordreset.tokens import get_token_generator

STATE_CHOICES = (
    ('basket', 'Статус корзины'),
    ('new', 'Новый'),
    ('confirmed', 'Подтвержден'),
    ('assembled', 'Собран'),
    ('sent', 'Отправлен'),
    ('delivered', 'Доставлен'),
    ('canceled', 'Отменен'),
)


class UserManager(BaseUserManager):

    use_in_migration = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('Укажите адрес электронной почты.')

        if not password:
            raise ValueError('Укажите пароль.')

        email = self.normalize_email(email)
        user = self.model(email=email, password=password, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)



class User(AbstractUser):
    REQUIRED_FIELDS = []
    objects = UserManager()
    USERNAME_FIELD = ['email']
    first_name = models.CharField(max_length=150, verbose_name='Имя')
    last_name = models.CharField(max_length=150, verbose_name='Фамилия')
    email = models.EmailField(verbose_name='Адрес электронной почты', unique=True)
    company = models.CharField(max_length=200, verbose_name='Компания', blank=True, null=True)
    position = models.CharField(max_length=200, verbose_name='Должность', blank=True, null=True)
    username_validator = UnicodeUsernameValidator()
    username = models.CharField(max_length=150, unique=True,
                                help_text=_('Имя не должно быть длинее 150 символов, должно содержать  цифры и символы @/./+/-/_'),
                                validators=[username_validator],
                                error_messages={'unique': _("Пользователь с таким именем уже создан.")})
    type = models.CharField(max_length=200, verbose_name='Тип пользователя',
                            choices=[('buyer', 'Покупатель'), ('shop', 'Магазин')],
                            default='buyer')

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['email']


    def __str__(self):
        return f'{self.first_name} {self.last_name}'



class Shop(models.Model):
    name = models.CharField(max_length=200, verbose_name='Магазин', unique=True)
    url = models.URLField(verbose_name='Ссылка на магазин')
    status = models.BooleanField(default=True, verbose_name=_('Статус получения заказов'))

    class Meta:
        verbose_name = 'Магазин'
        verbose_name_plural = 'Магазины'
        ordering = ['name']


    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=200, verbose_name='Категория')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, verbose_name='Магазин', related_name='categories')

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название товара')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='Категория', related_name='products')

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['name']

    def __str__(self):
        return self.name



class ProductInfo(models.Model):
    model = models.CharField(max_length=200, verbose_name='Модель', blank=False, null=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Товар', related_name='product_info')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='Категория',
                                 related_name='product_info')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, verbose_name='Магазин', related_name='product_info')
    quantity = models.PositiveIntegerField(verbose_name='Количество', blank=False, null=False)
    price = models.PositiveIntegerField (verbose_name='Цена', blank=False, null=False)

    class Meta:
        verbose_name = 'Информация о товаре'
        verbose_name_plural = 'Информация о товарах'
        ordering = ['model']
        constraint = models.UniqueConstraint(fields=['model', 'product', 'category','shop'], name='unique_product_info')


    def __str__(self):
        return self.model


class Parameter(models.Model):
    name = models.CharField(max_length=200, verbose_name='Параметр')

    class Meta:
        verbose_name = 'Параметр'
        verbose_name_plural = 'Параметры'
        ordering = ['name']

    def __str__(self):
        return self.name


class ProductParameter(models.Model):
    product_info = models.ForeignKey(ProductInfo, on_delete=models.CASCADE, verbose_name='Информация о товаре',
                                     related_name='product_parameters')
    parameter = models.ForeignKey(Parameter, on_delete=models.CASCADE, verbose_name='Параметр',
                                  related_name='product_parameters')
    value = models.CharField(max_length=200, verbose_name='Значение')

    class Meta:
        verbose_name = 'Параметр товара'
        verbose_name_plural = 'Параметры товаров'
        constraint = models.UniqueConstraint(fields=['product_info', 'parameter'], name='unique_product_parameter')


class UserInfo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь', related_name='user_info',
                             blank=True, null=True)
    city = models.CharField(max_length=200, verbose_name='Город')
    street = models.CharField(max_length=200, verbose_name='Улица')
    house_number = models.CharField(max_length=200, verbose_name='Номер дома', blank=True)
    flat_number = models.CharField(max_length=200, verbose_name='Номер квартиры', blank=True)
    phone = models.CharField(max_length=200, verbose_name='Телефон')

    class Meta:
        verbose_name = 'Информация о пользователе'
        verbose_name_plural = 'Информация о пользователях'
        ordering = ['city']

    def __str__(self):
        return f'{self.city}, {self.street}, дом {self.house_number}, квартира {self.flat_number}'


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             verbose_name='Пользователь', related_name='orders')
    user_info = models.ForeignKey(UserInfo, on_delete=models.CASCADE,
                                  verbose_name='Информация о пользователе', related_name='orders')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    status = models.CharField(choices=STATE_CHOICES, verbose_name='Статус заказа', max_length=20)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']


    def __str__(self):
        return f'{self.created_at}'


class OrderInfo(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, verbose_name='Заказ', related_name='order_info')
    product_info = models.ForeignKey(ProductInfo, on_delete=models.CASCADE, verbose_name='Информация о товаре',
                                     related_name='order_info')
    quantity = models.PositiveIntegerField(verbose_name='Количество')

    class Meta:
        verbose_name = 'Информация о заказе'
        verbose_name_plural = 'Информация о заказах'
        constraint = models.UniqueConstraint(fields=['order_id', 'product_info'], name='unique_order_info')


class EmailToken(models.Model):

    @staticmethod
    def generate_token():
        return get_token_generator().generate_token()

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_tokens',
                             verbose_name=_('Пользователь, который связан с токеном'))
    token = models.CharField(max_length=64, unique=True, db_index=True, verbose_name=_('Токен'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Дата создания'))

    class Meta:
        verbose_name = 'Токен для подтверждения аккаунта'
        verbose_name_plural = 'Токены для подтверждения аккаунтов'
        ordering = ['-created_at']


    def save(self, *args, **kwargs):
        if not self.token:
            self.token = self.generate_token()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f'Токен для подтверждения аккаунта {self.user}'
