# -*- coding: utf-8 -*-
from django import template
from opps.promos.models import Promo

register = template.Library()

@register.simple_tag
def get_active_promos(number=5, channel_slug=None,
                template_name='promos/actives.html'):

    active_promos = Promo.objects.all()
    if channel_slug:
        active_promos = active_promos.filter(channel__slug=channel_slug)

    active_promos = active_promos[:number]

    t = template.loader.get_template(template_name)

    return t.render(template.Context({'active_promos': active_promos,
                                      'channel_slug': channel_slug,
                                      'number': number}))
