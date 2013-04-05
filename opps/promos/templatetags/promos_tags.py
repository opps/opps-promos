# -*- coding: utf-8 -*-
from django import template
from django.conf import settings
from django.utils import timezone
from opps.promos.models import Promo, PromoBox

register = template.Library()

@register.simple_tag
def get_active_promos(number=5, channel_slug=None,
                template_name='promos/actives.html'):

    active_promos = Promo.objects.all_opened()
    if channel_slug:
        active_promos = active_promos.filter(channel__slug=channel_slug)

    active_promos = active_promos[:number]

    t = template.loader.get_template(template_name)

    return t.render(template.Context({'active_promos': active_promos,
                                      'channel_slug': channel_slug,
                                      'number': number}))

@register.simple_tag
def get_promobox(slug, channel_slug=None, template_name=None):
    if channel_slug:
        slug = u"{0}-{1}".format(slug, channel_slug)

    try:
        box = PromoBox.objects.get(site=settings.SITE_ID, slug=slug,
                                     date_available__lte=timezone.now(),
                                     published=True)
    except PromoBox.DoesNotExist:
        box = None

    t = template.loader.get_template('promos/promobox_detail.html')
    if template_name:
        t = template.loader.get_template(template_name)

    return t.render(template.Context({'promobox': box, 'slug': slug}))


@register.simple_tag
def get_all_promobox(channel_slug, template_name=None):
    boxes = PromoBox.objects.filter(site=settings.SITE_ID,
                                      date_available__lte=timezone.now(),
                                      published=True,
                                      channel__slug=channel_slug)

    t = template.loader.get_template('promos/promobox_list.html')
    if template_name:
        t = template.loader.get_template(template_name)

    return t.render(template.Context({'promoboxes': boxes}))
