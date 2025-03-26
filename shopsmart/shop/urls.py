from django.urls import path, include
from .views import (PartnerUpdate, LoginUserView, RegisterUser, BasketOfGoodsView, CategoryView, ShopView,
                   ProductInfoView, UserInfoView, OrderView, ConfirmEmailView, UserContactView)


urlpatterns = [
    path('partner/update/', PartnerUpdate.as_view(), name='partner_update'),
    path('user/login/', LoginUserView.as_view(), name='login'),
    path('user/register/', RegisterUser.as_view(), name='register'),
    path('basket/', BasketOfGoodsView.as_view(), name='basket'),
    path('categories/', CategoryView.as_view(), name='categories'),
    path('shops/', ShopView.as_view(), name='shops'),
    path('product/info', ProductInfoView.as_view(), name='products'),
    path('user/info', UserInfoView.as_view(), name='user_info'),
    path('order/', OrderView.as_view(), name='order'),
    path('user/register/confirm_email/', ConfirmEmailView.as_view(), name='confirm_email'),
    path('user/contact/', UserContactView.as_view(), name='user_contact'),
    path('auth/', include('social_django.urls', namespace='social')),
]
