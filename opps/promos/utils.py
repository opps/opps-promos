# coding: utf-8

import datetime
from django.template.response import TemplateResponse

def set_cookie(response, key, value, days_expire = 90):
    if days_expire is None:
        max_age = 365 * 24 * 60 * 60    #one year
    else:
        max_age = days_expire * 24 * 60 * 60
    expires = datetime.datetime.strftime(datetime.datetime.utcnow() + datetime.timedelta(seconds=max_age), "%a, %d-%b-%Y %H:%M:%S GMT")
    response.set_cookie(key, value, max_age=max_age, expires=expires)


class CookedResponse(TemplateResponse):
    def __init__(self, request, template, context=None, content_type=None,
            status=None, mimetype=None, current_app=None, cookie=None):
        self._request = request
        self._current_app = current_app

        super(TemplateResponse, self).__init__(
            template, context, content_type, status, mimetype)

        if cookie:
            set_cookie(self, *cookie)