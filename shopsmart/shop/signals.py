from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.dispatch import Signal, receiver
from django.template.defaultfilters import title

from .models import User


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
