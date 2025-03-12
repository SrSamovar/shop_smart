from celery import  shared_task
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

@shared_task
def send_email_task(user_email, subject, message):
    msg = EmailMultiAlternatives(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [user_email],
    )
    msg.send()
