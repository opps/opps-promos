#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf import settings
from django.http import Http404
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.contrib.sites.models import get_current_site, Site
from django.db.models import Q

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
        return promos.filter(
            Q(mirror_site__domain=site.domain) |
            Q(site__domain=site.domain)
        ).distinct()


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

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        context = super(PromoDetail, self).get_context_data(**kwargs)

        context['answers'] = self.object.answers
        context['request'] = self.request
        context['winners'] = self.object.winners

        context['answered'] = self.object.has_answered(request.user)

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
        if self.object.has_answered(request.user):
            context['error'] = _(u" You already answered this promo")
            return self.render_to_response(context)

        answer = request.POST.get('answer')
        answer_url = request.POST.get('answer_url')

        try:
            answer_file = request.FILES['answer_file']
        except:
            answer_file = None

        if not request.POST.get('agree'):
            context['error'] = _(u" You have to agree with the rules")
            return self.render_to_response(context)
        elif any((answer, answer_url, answer_file)):
            instance = Answer(
                user=request.user,
                promo=self.object,
                answer=answer
            )
        elif self.object.form_type == 'none':
            instance = Answer(
                user=request.user,
                promo=self.object
            )
        else:
            context['error'] = _(u" You have to fill the form")
            return self.render_to_response(context)

        if answer_url:
            instance.answer_url = answer_url

        if answer_file:
            instance.answer_file.save(answer_file._name, answer_file, True)

        instance.save()
        context['success'] = instance

        # send confirmation email
        if self.object.send_confirmation_email:
            subject = _(u"You are now registered for %s.") % self.object.title
            if getattr(settings, "OPPS_PROMO_CELERY_ENABLED", True):
                send_confirmation_email.delay(subject,
                                              self.object, request.user)
            else:
                send_confirmation_email(subject, self.object, request.user)

        return self.render_to_response(context)
