from typing import Type
from .tasks import send_email_task
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
    send_email_task.delay(user.email, 'Новый заказ', 'Ваш заказ сформирован')


@receiver(post_save, sender=User)
def new_user_registered_signal(sender: Type[User], instance: User, created: bool, **kwargs):
    """
     отправляем письмо с подтрердждением почты
    """
    if created and not instance.is_active:
        # send an e-mail to the user
        token, _ = EmailToken.objects.get_or_create(user_id=instance.pk)
        send_email_task.delay(instance.email,'Подтверждение электронной почты', token.key)
