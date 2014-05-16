# -*- coding: utf-8 -*-
from django import forms
from django.contrib import admin
#from django.contrib.admin.widgets import FilteredSelectMultiple
#from django.contrib.sites.models import Site
from django.utils.translation import ugettext_lazy as _

from opps.contrib.multisite.admin import AdminViewPermission
from opps.core.admin import PublishableAdmin
from opps.core.admin import apply_opps_rules
from opps.core.widgets import OppsEditor
from opps.images.generate import image_url

from .models import Promo, Answer, PromoContainer

from import_export import resources
from import_export.admin import ImportExportModelAdmin


class PromoAdminForm(forms.ModelForm):

    class Meta:
        model = Promo
        widgets = {
            "headline": OppsEditor(),
            "description": OppsEditor(),
            "confirmation_email_html": OppsEditor(),
            "rules": OppsEditor(),
            "result": OppsEditor()
        }


@apply_opps_rules('promos')
class PromoContainerInline(admin.TabularInline):
    model = PromoContainer
    fk_name = 'promo'
    raw_id_fields = ['container']
    actions = None
    extra = 1
    classes = ('collapse',)
    verbose_name = _(u'Promo Container')
    verbose_name_plural = _(u'Promo Containers')


@apply_opps_rules('promos')
class PromoAdmin(PublishableAdmin, AdminViewPermission):
    form = PromoAdminForm
    prepopulated_fields = {"slug": ["title"]}
    list_display = ['title', 'channel', 'date_available',
                    'date_end', 'site', 'published', 'preview_url']
    list_filter = ["date_end", "date_available", "published", "channel"]
    search_fields = ["title", "headline", "description"]
    exclude = ('user',)
    raw_id_fields = ['main_image', 'banner', 'channel']
    inlines = [PromoContainerInline]

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
                       'display_answers',
                       'countdown_enabled',
                       'mirror_site')}),

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
                image_url(obj.banner.archive.url, width=60, height=60))
        return _(u'No Image')
    banner_thumb.short_description = _(u'Thumbnail')
    banner_thumb.allow_tags = True


class AnswerResource(resources.ModelResource):

    def dehydrate_is_winner(self, obj):
        return u'Sim' if obj.is_winner else u'Não'

    def dehydrate_published(self, obj):
        return u'Sim' if obj.published else u'Não'

    def dehydrate_date_insert(self, obj):
        return obj.date_insert.strftime('%d/%m/%Y %H:%m')

    def dehydrate_answer(self, obj):
        return obj.answer or obj.answer_url or _('File')

    class Meta:
        model = Answer
        fields = ('promo__title', 'answer', 'user__email', 'published',
                  'is_winner', 'date_insert')


@apply_opps_rules('promos')
class AnswerAdmin(AdminViewPermission, ImportExportModelAdmin):
    resource_class = AnswerResource
    site_lookup = 'promo__site_iid__in'
    list_display = ['promo', 'user', 'answer', 'date_insert',
                    'published', 'is_winner', 'image_thumb']
    list_filter = ["promo", "date_insert", "published", 'is_winner']
    search_fields = ["answer", "user__email", "answer_url"]
    raw_id_fields = ['promo', 'user']

    def image_thumb(self, obj):
        return obj.get_file_display()
    image_thumb.short_description = _(u'Upload')
    image_thumb.allow_tags = True


admin.site.register(Promo, PromoAdmin)
admin.site.register(Answer, AnswerAdmin)
