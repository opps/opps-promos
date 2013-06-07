# -*- coding: utf-8 -*-
from django.contrib import admin
from django.utils import timezone
from django import forms
from django.utils.translation import ugettext_lazy as _

from redactor.widgets import RedactorEditor

from .models import (Promo, Answer, PromoPost, PromoBox,
                     PromoBoxPromos, PromoConfig)

from opps.core.admin import PublishableAdmin
from opps.core.admin import apply_opps_rules
from opps.images.generate import image_url


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


@apply_opps_rules('promos')
class PromoPostInline(admin.TabularInline):
    model = PromoPost
    fk_name = 'promo'
    raw_id_fields = ['post']
    actions = None
    extra = 1
    classes = ('collapse',)


@apply_opps_rules('promos')
class PromoAdmin(PublishableAdmin):
    form = PromoAdminForm
    prepopulated_fields = {"slug": ["title"]}
    list_display = ['title', 'channel', 'date_available',
                    'date_end', 'published', 'preview_url']
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
            'fields': (('main_image', 'image_thumb'), ('banner', 'banner_thumb'), 'tags')}),

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
                       'order', 'form_type',
                       'display_answers')}),

        (_(u'Participation'), {
            'fields': ('send_confirmation_email', 'confirmation_email_txt',
                       "confirmation_email_html", "confirmation_email_address")}),

        (_(u'Result'), {
            'classes': ('extrapretty'),
            'fields': ('result', 'display_winners')}),
    )

    readonly_fields = ['image_thumb', 'banner_thumb']

    def banner_thumb(self, obj):
        if obj.banner:
            return u'<img width="60px" height="60px" src="{0}" />'.format(
                image_url(obj.banner.image.url, width=60, height=60))
        return _(u'No Image')
    banner_thumb.short_description = _(u'Thumbnail')
    banner_thumb.allow_tags = True


@apply_opps_rules('promos')
class AnswerAdmin(admin.ModelAdmin):
    list_display = ['promo', 'user', 'date_insert',
                    'published', 'is_winner', 'image_thumb']
    list_filter = ["promo", "date_insert", "published", 'is_winner']
    search_fields = ["answer", "answer_url", "user"]
    raw_id_fields = ['promo', 'user']

    def image_thumb(self, obj):
        return obj.get_file_display()
    image_thumb.short_description = _(u'Upload')
    image_thumb.allow_tags = True


@apply_opps_rules('promos')
class PromoBoxPromosInline(admin.TabularInline):
    model = PromoBoxPromos
    fk_name = 'promobox'
    raw_id_fields = ['promo']
    actions = None
    extra = 1
    ordering = ('order',)
    fieldsets = [(None, {
        'classes': ('collapse',),
        'fields': ('promo', 'order', 'date_available', 'date_end')})]


@apply_opps_rules('promos')
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

    def clean_ended_entries(self, request, queryset):
        now = timezone.now()
        for box in queryset:
            ended = box.promoboxpromos_promoboxes.filter(
                date_end__lt=now
            )
            if ended:
                ended.delete()
    clean_ended_entries.short_description = _(u'Clean ended promos')

    actions = ('clean_ended_entries',)


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
