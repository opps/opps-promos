#!/usr/bin/env python
# -*- coding: utf-8 -*-
from importlib import import_module

from django.conf import settings
from django.http import Http404
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.shortcuts import get_object_or_404
from django.contrib.auth.views import redirect_to_login
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.contrib.sites.models import get_current_site, Site
from django.db.models import Q
from django.forms.formsets import formset_factory

from opps.channels.models import Channel

from .models import Promo, Answer
from .tasks import send_confirmation_email

if not 'endless_pagination' in settings.INSTALLED_APPS:
    settings.INSTALLED_APPS += (
        'endless_pagination',
    )


class PromoList(ListView):

    context_object_name = "promos"

    @property
    def template_name(self):
        return 'promos/promo_list.html'

    @property
    def queryset(self):
        site = get_current_site(self.request)
        promos = Promo.objects.all_opened()
        long_slug = self.request.path.strip('/')
        self.channel = get_object_or_404(
            Channel, site=site.id, long_slug=long_slug)
        return promos.filter(
            Q(mirror_site__domain=site.domain) |
            Q(site=site.id)
        ).distinct()

    def get_context_data(self, *args, **kwargs):
        import ipdb; ipdb.set_trace()
        context = super(PromoList, self).get_context_data(*args, **kwargs)
        context['channel'] = self.channel
        return context


class ChannelPromoList(ListView):

    context_object_name = "promos"

    def __init__(self, *args, **kwargs):
        self.channel = None
        super(ChannelPromoList, self).__init__(*args, **kwargs)

    @property
    def template_name(self):
        long_slug = self.kwargs.get('channel__long_slug')
        return 'promos/{0}.html'.format(long_slug)

    @property
    def queryset(self):
        site = get_current_site(self.request)
        long_slug = self.kwargs['channel__long_slug'].strip('/')
        self.channel = get_object_or_404(Channel, long_slug=long_slug)

        return Promo.objects.filter(
            channel__long_slug=long_slug,
            published=True,
            date_available__lte=timezone.now()
        ).filter(
            Q(mirror_site__domain=site.domain) |
            Q(site__domain=site.domain)
        ).distinct()

    def get_context_data(self, *args, **kwargs):
        context = super(ChannelPromoList, self).get_context_data(*args,
                                                                 **kwargs)
        context['channel'] = self.channel
        return context


class PromoDetail(DetailView):

    context_object_name = "promo"
    model = Promo

    def get_template_names(self):
        """
        Return a list of template names to be used for the request. Must return
        a list. May not be called if get_template is overridden.
        """
        names = []

        if not self.object.is_opened:
            self.template_name_suffix = "_closed"

        if hasattr(self.object, '_meta'):
            app_label = self.object._meta.app_label
            object_name = self.object._meta.object_name.lower()
        elif hasattr(self, 'model') and hasattr(self.model, '_meta'):
            app_label = self.model._meta.app_label
            object_name = self.model._meta.object_name.lower()

        if self.object.channel:
            long_slug = self.object.channel.long_slug
            # 1. try channel/promo template
            # promos/channel-slug/promo-slug.html
            names.append('{0}/{1}/{2}.html'.format(
                app_label, long_slug, self.kwargs['slug']
            ))
            # 2. try a generic channel template
            # promos/channel-slug/<model>_detail.html
            names.append('{0}/{1}/{2}{3}.html'.format(
                app_label, long_slug, object_name, self.template_name_suffix
            ))

        # 3. try promo template (all channels)
        # promos/promo-slug.html
        names.append('{0}/{1}.html'.format(
            app_label, self.kwargs['slug']
        ))

        # The least-specific option is the default <app>/<model>_detail.html;
        # only use this if the object in question is a model.
        if hasattr(self.object, '_meta'):
            names.append("%s/%s%s.html" % (
                self.object._meta.app_label,
                self.object._meta.object_name.lower(),
                self.template_name_suffix
            ))
        elif hasattr(self, 'model') and hasattr(self.model, '_meta'):
            names.append("%s/%s%s.html" % (
                self.model._meta.app_label,
                self.model._meta.object_name.lower(),
                self.template_name_suffix
            ))

        return names

    def get_object(self):
        self.fallback = getattr(settings, 'OPPS_MULTISITE_FALLBACK', False)
        self.site = get_current_site(self.request)
        self.site_master = Site.objects.order_by('id')[0]

        filters = dict(slug=self.kwargs['slug'], site=self.site)
        preview_enabled = self.request.user and self.request.user.is_staff
        if not preview_enabled:
            filters['date_available__lte'] = timezone.now()
            filters['published'] = True

        try:
            return Promo.objects.get(**filters)
        except Promo.DoesNotExist:
            if self.fallback:
                filters.pop('site', None)
                promos = Promo.objects.filter(
                    **filters
                ).filter(
                    Q(mirror_site__domain=self.site.domain) |
                    Q(site__domain=self.site.domain)
                ).distinct()
                try:
                    return promos.order_by('-date_available')[0]
                except IndexError:
                    # raises final Http404
                    pass

        raise Http404(u"Promo object does not exist")

    def userformset_factory(self, cls):
        return formset_factory(cls, max_num=1, extra=1, can_delete=False)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        context = super(PromoDetail, self).get_context_data(**kwargs)

        context['answers'] = self.object.answers
        context['request'] = self.request
        context['winners'] = self.object.winners

        context['answered'] = self.object.has_answered(request.user)

        AnswerForm = self.object.get_answer_form()
        form = AnswerForm()

        if not request.user.is_authenticated() and \
                not self.object.login_required:
            AnonyUserForm = self.object.get_anony_user_form()
            AnonyUserFormSet = self.userformset_factory(AnonyUserForm)
            context['user_formset'] = AnonyUserFormSet()

        context['form'] = form

        if self.object.channel:
            context['channel'] = self.object.channel

        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        context = self.get_context_data(**kwargs)
        context['answers'] = self.object.answers
        context['request'] = request
        if self.object.channel:
            context['channel'] = self.object.channel

        # check if is_closed or not published
        if not self.object.is_opened or not self.object.published:
            context['error'] = _(u"Promo not opened")
            return self.render_to_response(context)

        # check if already answered
        if self.object.login_required and \
                self.object.has_answered(request.user):
            context['error'] = _(u"You already answered this promo")
            return self.render_to_response(context)

        AnswerForm = self.object.get_answer_form()

        form = AnswerForm(request.POST, request.FILES)
        is_valid = [form.is_valid()]

        if not request.user.is_authenticated() and \
                not self.object.login_required:
            AnonyUserForm = self.object.get_anony_user_form()
            AnonyUserFormSet = self.userformset_factory(AnonyUserForm)
            user_formset = AnonyUserFormSet(request.POST, request.FILES)
            is_valid.append(user_formset.is_valid())
            context['user_formset'] = user_formset

        if all(is_valid):
            instance = form.save(commit=False)

            if request.user.is_authenticated():
                instance.user = request.user
            else:
                user_anony_data = user_formset.cleaned_data[0]
                user_anony_data.update({
                    '__form__module__': AnonyUserForm.__module__,
                    '__form__name__': AnonyUserForm.__name__})

                instance.user_anony_data = user_anony_data

            instance.promo = self.object
            instance.save()
            context['success'] = instance
        else:
            context['form'] = form
            context['error'] = form.non_field_errors()
            return self.render_to_response(context)

        context['form'] = form
        # send confirmation email
        if self.object.send_confirmation_email:
            subject = _(u"You are now registered for %s.") % self.object.title
            if getattr(settings, "OPPS_PROMO_CELERY_ENABLED", True):
                send_confirmation_email.delay(subject,
                                              self.object, request.user)
            else:
                send_confirmation_email(subject, self.object, request.user)

        return self.render_to_response(context)
