from celery import  shared_task
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from easy_thumbnails.files import get_thumbnailer, generate_all_aliases


@shared_task
def send_email_task(user_email, subject, message):
    msg = EmailMultiAlternatives(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [user_email],
    )
    msg.send()

@shared_task()
def generate_thumbnails(model, pk, field):
    instance = model._default_manager.get(pk=pk)
    fieldfile = getattr(instance, field)
    generate_all_aliases(fieldfile, include_global=True)