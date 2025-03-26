from django import forms
from easy_thumbnails.fields import ThumbnailerImageField

from .models import User, Product, Shop

class UserForms(forms.ModelForm):

    class Meta:
        model = User
        fields = ('email', 'image' , 'first_name', 'last_name', 'type', 'company','position')


class ProductForms(forms.ModelForm):

    class Meta:
        model = Product
        fields = ('name', 'image', 'category')


class ShopForms(forms.ModelForm):

    class Meta:
        model = Shop
        fields = ('name', 'url', 'status', 'image')


class ImageForm(forms.Form):
    image = ThumbnailerImageField(upload_to='images/')
