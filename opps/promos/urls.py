#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from django.conf.urls import patterns, url

from .views import PromoDetail, PromoList, ChannelPromoList


urlpatterns = patterns(
    '',
    url(
        r'^$',
        PromoList.as_view(),
        name='list_promos'
    ),
    url(
        r'^channel/(?P<channel__long_slug>[\w//-]+)$',
        ChannelPromoList.as_view(),
        name='channel_promo'
    ),
    url(
        r'^(?P<slug>[\w-]+)/(?P<result>[\w-]+)$',
        PromoDetail.as_view(),
        name='result_promo'
    ),
    url(
        r'^(?P<slug>[\w-]+)\.html$',
        PromoDetail.as_view(),
        name='open_promo'
    ),
)
