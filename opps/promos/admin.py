# -*- coding: utf-8 -*-
from django.contrib import admin
from django import forms
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.utils.translation import ugettext_lazy as _

from redactor.widgets import RedactorEditor

from .models import Promo, Answer, PromoPost


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


class PromoAdmin(admin.ModelAdmin):
    form = PromoAdminForm
    prepopulated_fields = {"slug": ["title"]}
    list_display = ['title', 'channel', 'date_available', 'date_end', 'published']
    list_filter = ["date_end", "date_available", "published", "channel"]
    search_fields = ["title", "headline", "description"]
    exclude = ('user',)
    raw_id_fields = ['main_image', 'channel']
    inlines = [PromoPostInline]

    fieldsets = (
        (_(u'Identification'), {
            'fields': ('title', 'slug')}),
        (_(u'Content'), {
            'classes': ('extrapretty'),
            'fields': ('main_image', 'tags')}),

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
            'fields': ('published', 'date_available', 'date_end',
                'position', 'has_upload','has_urlfield', 'template_path')}),
        (_(u'Participation'), {
            'fields': ('send_confirmation_email', 'confirmation_email_txt',
                "confirmation_email_html", "confirmation_email_address")}),
        (_(u'Result'), {
            'fields': ('result', 'display_winners')}),
    )

    def save_model(self, request, obj, form, change):
        try:
            obj.site = obj.channel.site if obj.channel else Site.objects.get(pk=1)
            if obj.user:
                pass
        except User.DoesNotExist:
            obj.user = request.user

        super(PromoAdmin, self).save_model(request, obj, form, change)


class AnswerAdmin(admin.ModelAdmin):
    list_display = ['promo', 'user', 'date_insert', 'published', 'is_winner']
    list_filter = ["promo", "date_insert", "published", 'is_winner']
    search_fields = ["answer", "answer_url", "user"]
    raw_id_fields = ['promo', 'user']


admin.site.register(Promo, PromoAdmin)
admin.site.register(Answer, AnswerAdmin)