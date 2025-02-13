from django.contrib import admin
from .models import User, UserInfo, Shop, Category, OrderInfo, Order, ProductInfo, ProductParameter, Parameter, \
    EmailToken, Product


# @admin.register(UserInfo)
# class UserInfoAdmin(admin.TabularInline):
#     pass


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_staff', 'is_active', 'type')
    list_filter = ('is_staff', 'is_active', 'type')


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    pass


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    pass


@admin.register(OrderInfo)
class OrderInfoAdmin(admin.ModelAdmin):
    pass



@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    pass



@admin.register(ProductInfo)
class ProductInfoAdmin(admin.ModelAdmin):
    pass



@admin.register(ProductParameter)
class ProductParameterAdmin(admin.ModelAdmin):
    pass


@admin.register(Parameter)
class ParameterAdmin(admin.ModelAdmin):
    pass



@admin.register(EmailToken)
class EmailTokenAdmin(admin.ModelAdmin):
    pass


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    pass
