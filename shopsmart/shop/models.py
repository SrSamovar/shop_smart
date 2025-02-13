from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.utils.translation import gettext_lazy as _
from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
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

USER_TYPE_CHOICES = (
    ('buyer', 'Покупатель'),
    ('shop', 'Магазин'),
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
    """
    Стандартная модель пользователей
    """
    REQUIRED_FIELDS = []
    objects = UserManager()
    USERNAME_FIELD = 'email'
    email = models.EmailField(_('email address'), unique=True)
    company = models.CharField(verbose_name='Компания', max_length=40, blank=True)
    position = models.CharField(verbose_name='Должность', max_length=40, blank=True)
    username_validator = UnicodeUsernameValidator()
    groups = models.ManyToManyField(Group, related_name='shop_users_groups', verbose_name='группы')
    user_permissions = models.ManyToManyField(Permission, related_name='shop_users_permissions', verbose_name='разрешения')
    username = models.CharField(
        _('username'),
        max_length=150,
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        validators=[username_validator],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    is_active = models.BooleanField(
        _('active'),
        default=False,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    type = models.CharField(verbose_name='Тип пользователя', choices=USER_TYPE_CHOICES, max_length=5, default='buyer')

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = "Список пользователей"
        ordering = ('email',)



class Shop(models.Model):
    objects = models.manager.Manager()
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
    objects = models.manager.Manager()
    name = models.CharField(max_length=200, verbose_name='Категория')
    shop = models.ManyToManyField(Shop, related_name='categories', verbose_name='магазины')

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Product(models.Model):
    objects = models.manager.Manager()
    name = models.CharField(max_length=200, verbose_name='Название товара')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='Категория', related_name='products')

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ('name',)

    def __str__(self):
        return self.name



class ProductInfo(models.Model):
    objects = models.manager.Manager()
    model = models.CharField(max_length=200, verbose_name='Модель', blank=False, null=False)
    external_id = models.PositiveIntegerField(verbose_name='Внешний идентификатор')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Товар', related_name='product_info')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, verbose_name='Магазин', related_name='product_info')
    quantity = models.PositiveIntegerField(verbose_name='Количество', blank=False, null=False)
    price = models.PositiveIntegerField (verbose_name='Цена', blank=False, null=False)
    price_rrc = models.PositiveIntegerField(verbose_name='Розничная цена')

    class Meta:
        verbose_name = 'Информация о товаре'
        verbose_name_plural = 'Информация о товарах'
        ordering = ('model',)
        constraints = [models.UniqueConstraint(fields=['product', 'external_id','shop'], name='unique_product_info')]



class Parameter(models.Model):
    objects = models.manager.Manager()
    name = models.CharField(max_length=200, verbose_name='Параметр')

    class Meta:
        verbose_name = 'Параметр'
        verbose_name_plural = 'Параметры'
        ordering = ('name',)

    def __str__(self):
        return self.name


class ProductParameter(models.Model):
    objects = models.manager.Manager()
    product_info = models.ForeignKey(ProductInfo, on_delete=models.CASCADE, verbose_name='Информация о товаре',
                                     related_name='product_parameters')
    parameter = models.ForeignKey(Parameter, on_delete=models.CASCADE, verbose_name='Параметр',
                                  related_name='product_parameters')
    value = models.CharField(max_length=200, verbose_name='Значение')

    class Meta:
        verbose_name = 'Параметр товара'
        verbose_name_plural = 'Параметры товаров'
        constraints = [models.UniqueConstraint(fields=['product_info', 'parameter'], name='unique_product_parameter')]


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
        ordering = ('city',)

    def __str__(self):
        return f'{self.city}, {self.street}, дом {self.house_number}, квартира {self.flat_number}'


class Order(models.Model):
    objects = models.manager.Manager()
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
    objects = models.manager.Manager()
    order = models.ForeignKey(Order, on_delete=models.CASCADE, verbose_name='Заказ', related_name='order_info')
    product_info = models.ForeignKey(ProductInfo, on_delete=models.CASCADE, verbose_name='Информация о товаре',
                                     related_name='order_info')
    quantity = models.PositiveIntegerField(verbose_name='Количество')

    class Meta:
        verbose_name = 'Информация о заказе'
        verbose_name_plural = 'Информация о заказах'
        constraints = [models.UniqueConstraint(fields=['order_id', 'product_info'], name='unique_order_info')]


class EmailToken(models.Model):
    objects = models.manager.Manager()

    class Meta:
        verbose_name = 'Токен для подтверждения аккаунта'
        verbose_name_plural = 'Токены для подтверждения аккаунтов'


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
        ordering = ('-created_at',)


    def save(self, *args, **kwargs):
        if not self.token:
            self.token = self.generate_token()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f'Токен для подтверждения аккаунта {self.user}'
