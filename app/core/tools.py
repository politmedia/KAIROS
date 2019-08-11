from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.mail import send_mail
from django.utils.translation import gettext as _
from textwrap import dedent
import datetime
import json


def set_cookie(response, key, value, days_expire = 7):
    if days_expire is None:
        max_age = 365 * 24 * 60 * 60  # one year
    else:
        max_age = days_expire * 24 * 60 * 60
        expires = datetime.datetime.strftime(
            datetime.datetime.utcnow() + datetime.timedelta(seconds=max_age),
            '%a, %d-%b-%Y %H:%M:%S GMT'
        )
        response.set_cookie(
            key,
            json.dumps(value),
            max_age=max_age,
            expires=expires,
            domain=settings.SESSION_COOKIE_DOMAIN,
            secure=settings.SESSION_COOKIE_SECURE or None
        )


def get_cookie(request, key, default):
    strval = request.COOKIES.get(key)
    if strval:
        return json.loads(strval)
    return default


def send_mail_to_politician(request, politician):
        send_mail(
            str(_('Freedomvote account link')),
            dedent(str(_("""Hello %(first_name)s %(last_name)s,

            You receive the link for your profile on Freedomvote: %(url)s

            Keep this link and use it to login to your profile again.

            Sincerely,
            The Freedomvote Team""") % {
                'first_name': politician.first_name,
                'last_name': politician.last_name,
                'url': politician.unique_url
            })),
            settings.DEFAULT_FROM_EMAIL,
            [politician.email],
            fail_silently=False,
        )
