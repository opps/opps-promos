# -*- coding: utf-8 -*-
from django.contrib import admin
from django import forms
from django.utils.translation import ugettext_lazy as _

from redactor.widgets import RedactorEditor

from .models import (Promo, Answer, PromoPost, PromoBox,
                     PromoBoxPromos, PromoConfig)

from opps.core.admin import PublishableAdmin


class PromoAdminForm(forms.ModelForm):
    class Meta:
        model = Promo
        widgets = {
            "headline": RedactorEditor(),
            "description": RedactorEditor(),
            "confirmation_email_html": RedactorEditor(),
            "rules": RedactorEditor(),
            "result": RedactorEditor()
        }


class PromoPostInline(admin.TabularInline):
    model = PromoPost
    fk_name = 'promo'
    raw_id_fields = ['post']
    actions = None
    extra = 1
    classes = ('collapse',)


class PromoAdmin(PublishableAdmin):
    form = PromoAdminForm
    prepopulated_fields = {"slug": ["title"]}
    list_display = ['title', 'channel', 'date_available', 'date_end', 'published']
    list_filter = ["date_end", "date_available", "published", "channel"]
    search_fields = ["title", "headline", "description"]
    exclude = ('user',)
    raw_id_fields = ['main_image', 'banner', 'channel']
    inlines = [PromoPostInline]

    fieldsets = (
        (_(u'Identification'), {
            'fields': ('site', 'title', 'slug')}),

        (_(u'Content'), {
            'classes': ('extrapretty'),
            'fields': ('main_image', 'banner', 'tags')}),

        (_(u'Headline'), {
            'classes': ('extrapretty'),
            'fields': ('headline', )}),

        (_(u'Description'), {
            'classes': ('extrapretty'),
            'fields': ('description',)}),

        (_(u'Rules'), {
            'classes': ('extrapretty'),
            'fields': ('rules',)}),

        (_(u'Relationships'), {
            'fields': ('channel',)}),

        (_(u'Publication'), {
            'classes': ('extrapretty'),
            'fields': ('published', ('date_available', 'date_end'),
                       'order', 'has_upload', 'has_urlfield',
                       'display_answers')}),

        (_(u'Participation'), {
            'fields': ('send_confirmation_email', 'confirmation_email_txt',
                       "confirmation_email_html", "confirmation_email_address")}),

        (_(u'Result'), {
            'classes': ('extrapretty'),
            'fields': ('result', 'display_winners')}),
    )


class AnswerAdmin(admin.ModelAdmin):
    list_display = ['promo', 'user', 'date_insert', 'published', 'is_winner']
    list_filter = ["promo", "date_insert", "published", 'is_winner']
    search_fields = ["answer", "answer_url", "user"]
    raw_id_fields = ['promo', 'user']


class PromoBoxPromosInline(admin.TabularInline):
    model = PromoBoxPromos
    fk_name = 'promobox'
    raw_id_fields = ['promo']
    actions = None
    extra = 1
    fieldsets = [(None, {
        'classes': ('collapse',),
        'fields': ('promo', 'order')})]


class PromoBoxAdmin(PublishableAdmin):
    prepopulated_fields = {"slug": ["name"]}
    list_display = ['name', 'date_available', 'published']
    list_filter = ['date_available', 'published']
    inlines = [PromoBoxPromosInline]
    exclude = ('user',)
    raw_id_fields = ['channel', 'article']

    fieldsets = (
        (_(u'Identification'), {
            'fields': ('site', 'name', 'slug')}),
        (_(u'Relationships'), {
            'fields': (('channel', 'article'),)}),
        (_(u'Publication'), {
            'classes': ('extrapretty'),
            'fields': ('published', 'date_available')}),
    )


class PromoConfigAdmin(PublishableAdmin):
    list_display = ['key', 'key_group', 'channel', 'date_insert',
                    'date_available', 'published']
    list_filter = ["key", 'key_group', "channel", "published"]
    search_fields = ["key", "key_group", "value"]
    raw_id_fields = ['promo', 'channel', 'article']
    exclude = ('user',)


admin.site.register(Promo, PromoAdmin)
admin.site.register(Answer, AnswerAdmin)
admin.site.register(PromoBox, PromoBoxAdmin)
admin.site.register(PromoConfig, PromoConfigAdmin)
