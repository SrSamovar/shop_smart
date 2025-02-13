from typing import Type

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db.models.signals import post_save
from django.dispatch import Signal, receiver
from django.template.defaultfilters import title

from .models import User, EmailToken


new_order = Signal()





@receiver(new_order)
def new_order_signal(user_id, **kwargs):
    """
    Отправка письма при новом заказе
    """
    user = User.objects.get(id=user_id)
    msg = EmailMultiAlternatives(
        f'Обновление статуса заказа',
        f'Заказ сформирован',
        settings.EMAIL_HOST_USER,
        [user.email],
    )
    msg.send()


@receiver(post_save, sender=User)
def new_user_registered_signal(sender: Type[User], instance: User, created: bool, **kwargs):
    """
     отправляем письмо с подтрердждением почты
    """
    if created and not instance.is_active:
        # send an e-mail to the user
        token, _ = EmailToken.objects.get_or_create(user_id=instance.pk)

        msg = EmailMultiAlternatives(
            # title:
            f"Password Reset Token for {instance.email}",
            # message:
            token.key,
            # from:
            settings.EMAIL_HOST_USER,
            # to:
            [instance.email]
        )
        msg.send()
