# -*- coding: utf-8 -*-
from django import template
from django.conf import settings

from opps.promos.models import Promo


register = template.Library()


@register.assignment_tag
def get_promos_by(opened=True, exclude=False, **filters):
    """
        Return a list of promos filtered by given args

        Usage:

          {% get_promos_by opened=[True|False] exclude=[True|False]
             filter1=value filter2=value .. %}
    """

    qs = Promo.objects.all_opened()

    if not opened:
        qs = Promo.objects.all_closed()

    qs = qs.filter(site=settings.SITE_ID)

    if exclude:
        return qs.exclude(**filters)

    return qs.filter(**filters)
