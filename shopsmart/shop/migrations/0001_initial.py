# Generated by Django 5.1.5 on 2025-02-05 21:32

import django.contrib.auth.validators
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Категория')),
            ],
            options={
                'verbose_name': 'Категория',
                'verbose_name_plural': 'Категории',
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='Parameter',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Параметр')),
            ],
            options={
                'verbose_name': 'Параметр',
                'verbose_name_plural': 'Параметры',
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='Shop',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, unique=True, verbose_name='Магазин')),
                ('url', models.URLField(verbose_name='Ссылка на магазин')),
                ('status', models.BooleanField(default=True, verbose_name='Статус получения заказов')),
            ],
            options={
                'verbose_name': 'Магазин',
                'verbose_name_plural': 'Магазины',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Название товара')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products', to='shop.category', verbose_name='Категория')),
            ],
            options={
                'verbose_name': 'Товар',
                'verbose_name_plural': 'Товары',
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='ProductInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('model', models.CharField(max_length=200, verbose_name='Модель')),
                ('external_id', models.PositiveIntegerField(verbose_name='Внешний идентификатор')),
                ('quantity', models.PositiveIntegerField(verbose_name='Количество')),
                ('price', models.PositiveIntegerField(verbose_name='Цена')),
                ('price_rrc', models.PositiveIntegerField(verbose_name='Розничная цена')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='product_info', to='shop.product', verbose_name='Товар')),
                ('shop', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='product_info', to='shop.shop', verbose_name='Магазин')),
            ],
            options={
                'verbose_name': 'Информация о товаре',
                'verbose_name_plural': 'Информация о товарах',
                'ordering': ('model',),
            },
        ),
        migrations.AddField(
            model_name='category',
            name='shop',
            field=models.ManyToManyField(related_name='categories', to='shop.shop', verbose_name='магазины'),
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='email address')),
                ('company', models.CharField(blank=True, max_length=40, verbose_name='Компания')),
                ('position', models.CharField(blank=True, max_length=40, verbose_name='Должность')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('is_active', models.BooleanField(default=False, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('type', models.CharField(choices=[('buyer', 'Покупатель'), ('shop', 'Магазин')], default='buyer', max_length=5, verbose_name='Тип пользователя')),
                ('groups', models.ManyToManyField(related_name='shop_users_groups', to='auth.group', verbose_name='группы')),
                ('user_permissions', models.ManyToManyField(related_name='shop_users_permissions', to='auth.permission', verbose_name='разрешения')),
            ],
            options={
                'verbose_name': 'Пользователь',
                'verbose_name_plural': 'Список пользователей',
                'ordering': ('email',),
            },
        ),
        migrations.CreateModel(
            name='EmailToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(db_index=True, max_length=64, unique=True, verbose_name='Токен')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='email_tokens', to='shop.user', verbose_name='Пользователь, который связан с токеном')),
            ],
            options={
                'verbose_name': 'Токен для подтверждения аккаунта',
                'verbose_name_plural': 'Токены для подтверждения аккаунтов',
                'ordering': ('-created_at',),
            },
        ),
        migrations.CreateModel(
            name='UserInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('city', models.CharField(max_length=200, verbose_name='Город')),
                ('street', models.CharField(max_length=200, verbose_name='Улица')),
                ('house_number', models.CharField(blank=True, max_length=200, verbose_name='Номер дома')),
                ('flat_number', models.CharField(blank=True, max_length=200, verbose_name='Номер квартиры')),
                ('phone', models.CharField(max_length=200, verbose_name='Телефон')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='user_info', to='shop.user', verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Информация о пользователе',
                'verbose_name_plural': 'Информация о пользователях',
                'ordering': ('city',),
            },
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('status', models.CharField(choices=[('basket', 'Статус корзины'), ('new', 'Новый'), ('confirmed', 'Подтвержден'), ('assembled', 'Собран'), ('sent', 'Отправлен'), ('delivered', 'Доставлен'), ('canceled', 'Отменен')], max_length=20, verbose_name='Статус заказа')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orders', to='shop.user', verbose_name='Пользователь')),
                ('user_info', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orders', to='shop.userinfo', verbose_name='Информация о пользователе')),
            ],
            options={
                'verbose_name': 'Заказ',
                'verbose_name_plural': 'Заказы',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='OrderInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(verbose_name='Количество')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='order_info', to='shop.order', verbose_name='Заказ')),
                ('product_info', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='order_info', to='shop.productinfo', verbose_name='Информация о товаре')),
            ],
            options={
                'verbose_name': 'Информация о заказе',
                'verbose_name_plural': 'Информация о заказах',
                'constraints': [models.UniqueConstraint(fields=('order_id', 'product_info'), name='unique_order_info')],
            },
        ),
        migrations.CreateModel(
            name='ProductParameter',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.CharField(max_length=200, verbose_name='Значение')),
                ('parameter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='product_parameters', to='shop.parameter', verbose_name='Параметр')),
                ('product_info', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='product_parameters', to='shop.productinfo', verbose_name='Информация о товаре')),
            ],
            options={
                'verbose_name': 'Параметр товара',
                'verbose_name_plural': 'Параметры товаров',
                'constraints': [models.UniqueConstraint(fields=('product_info', 'parameter'), name='unique_product_parameter')],
            },
        ),
        migrations.AddConstraint(
            model_name='productinfo',
            constraint=models.UniqueConstraint(fields=('product', 'external_id', 'shop'), name='unique_product_info'),
        ),
    ]
