import celery
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.core.mail import EmailMultiAlternatives


@celery.task
def send_confirmation_email(subject, obj, user):

    DEFAULT_TXT = _(
        u"Thank you! "
        u"You are now inscribed to {obj.title}"
    ).format(obj=obj)

    msg = EmailMultiAlternatives(
        subject,
        obj.confirmation_email_txt or DEFAULT_TXT,
        obj.confirmation_email_address or settings.DEFAULT_FROM_EMAIL,
        [user.email]
    )
    msg.attach_alternative(
        obj.confirmation_email_html or DEFAULT_TXT,
        'text/html'
    )
    try:
        return msg.send()
    except:
        return None
