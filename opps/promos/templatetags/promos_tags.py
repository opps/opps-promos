# -*- coding: utf-8 -*-
from django import template
from django.conf import settings

from opps.promos.models import Promo


register = template.Library()


@register.assignment_tag
def get_promos_by(opened=True, **filters):
    """
        Return a list of promos filtered by given args

        Usage:

          {% get_promos_by opened=[True|False] filter1=value filter2=value .. %}
    """

    qs = Promo.objects.all_opened()

    if not opened:
        qs = Promo.objects.all_closed()

    return qs.filter(site=settings.SITE_ID,
                     **filters)
