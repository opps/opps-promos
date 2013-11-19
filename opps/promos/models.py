# -*- coding: utf-8 -*-

import os
import uuid

from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse

from opps.core.models import PublishableManager
from opps.images.models import Image
from opps.images.generate import image_url

from opps.containers.models import Container

app_namespace = getattr(settings, 'OPPS_PROMOS_URL_NAMESPACE', 'promos')


class PromoManager(PublishableManager):

    def all_opened(self):
        return super(PromoManager, self).get_query_set().filter(
            date_available__lte=timezone.now(),
            published=True
        ).filter(
            Q(date_end__gte=timezone.now()) | Q(date_end__isnull=True)
        )

    def all_closed(self):
        return super(PromoManager, self).get_query_set().filter(
            date_available__lte=timezone.now(),
            published=True,
            date_end__lte=timezone.now()
        )


class Promo(Container):

    FORM_TYPES = (
        ("none", _(u"Registration only")),

        ("text", _(u"Text only")),
        ("upload", _(u"Upload only")),
        ("url", _(u"Url only")),

        ("text|upload", _(u"Text and Upload")),
        ("text|url", _(u"Text and Url")),
        ("text|url|upload", _(u"Text, Url and Upload")),
    )

    headline = models.TextField(_(u"Headline"), blank=True)
    description = models.TextField(_(u"Description"), blank=True)

    rules = models.TextField(_(u'Rules'), blank=True)
    result = models.TextField(_(u'Result'), blank=True)

    containers = models.ManyToManyField(
        'containers.Container',
        null=True, blank=True,
        related_name='promo_container',
        through='PromoContainer'
    )

    banner = models.ForeignKey(Image,
                               verbose_name=_(u'Promo Banner'), blank=True,
                               null=True, on_delete=models.SET_NULL,
                               related_name='promo_banner',
                               help_text=_(u'300 x 498 banner image'))
    date_end = models.DateTimeField(_(u"End date"), null=True, blank=True)
    order = models.IntegerField(_(u"Order"), default=0)

    form_type = models.CharField(
        _(u"Form type"),
        max_length=20,
        choices=FORM_TYPES,
        default="text"
    )

    display_answers = models.BooleanField(_(u"Display answers?"), default=True)
    display_winners = models.BooleanField(_(u"Display winners?"), default=False)

    send_confirmation_email = models.BooleanField(
        _(u"Send confirmation email?"),
        default=False
    )
    confirmation_email_txt = models.TextField(
        _(u'Confirmation email (Text)'),
        blank=True
    )
    confirmation_email_html = models.TextField(
        _(u'Confirmation email (HTML)'),
        blank=True
    )
    confirmation_email_address = models.EmailField(
        _(u'Email'),
        max_length=255,
        null=True,
        blank=True
    )

    countdown_enabled = models.BooleanField(
        _(u"Countdown enabled"),
        default=True
    )

    @property
    def countdown(self):
        if self.date_end and self.countdown_enabled:
            now = timezone.now()
            delta = self.date_end - now
            return delta

    def get_form_type(self):
        try:
            return self.form_type.split('|')
        except:
            return [self.form_type]

    @property
    def has_upload(self):
        return 'upload' in self.get_form_type()

    @property
    def has_urlfield(self):
        return 'url' in self.get_form_type()

    @property
    def has_textfield(self):
        return 'text' in self.get_form_type()

    @property
    def is_opened(self):
        now = timezone.now()
        self.date_available = self.date_available or now
        if not self.date_end and self.date_available <= now:
            return True
        elif not self.date_end and self.date_available > now:
            return False
        return now >= self.date_available and now <= self.date_end

    @property
    def answers(self):
        return self.answer_set.filter(published=True)

    @property
    def winners(self):
        return self.answers.filter(is_winner=True)

    def has_answered(self, user):
        try:
            return self.answers.filter(user=user).exists()
        except TypeError:
            return False

    def __unicode__(self):
        return self.title

    objects = PromoManager()

    class Meta:
        ordering = ['order']
        verbose_name = _(u'Promo')
        verbose_name_plural = _(u'Promos')

    def get_absolute_url(self):
        return reverse(
            '{0}:open_promo'.format(app_namespace),
            kwargs={'slug': self.slug}
        )

    def get_thumb(self):
        return self.main_image

    @property
    def search_category(self):
        return _("Promo")


class PromoContainer(models.Model):
    container = models.ForeignKey(
        'containers.Container',
        verbose_name=_(u'Promo Container'),
        null=True,
        blank=True,
        related_name='promocontainer_container',
        on_delete=models.SET_NULL
    )
    promo = models.ForeignKey(
        Promo,
        verbose_name=_(u'Promo'),
        null=True,
        blank=True,
        related_name='promo',
        on_delete=models.SET_NULL
    )

    def __unicode__(self):
        return u"{0}-{1}".format(self.promo.slug, self.post.slug)

    class Meta:
        verbose_name = _(u'Promo Container')
        verbose_name_plural = _(u'Promo Containers')


def get_file_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = "{0}-{1}.{2}".format(uuid.uuid4(), instance.promo.slug, ext)
    d = timezone.now()
    folder = "promos/{0}".format(d.strftime("%Y/%m/%d/"))
    return os.path.join(folder, filename)


class Answer(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             verbose_name=_(u'User'))
    promo = models.ForeignKey(Promo, verbose_name=_(u'Promo'))
    answer = models.TextField(_(u"Answer"), blank=True, null=True)
    answer_url = models.URLField(_(u"Answer URL"), blank=True, null=True)
    answer_file = models.FileField(upload_to=get_file_path,
                                   verbose_name=_(u'Answer File'), blank=True,
                                   null=True)
    publish_file = models.BooleanField(
        _(u"Publish file?"),
        default=False,
        help_text=_(u'Show image thumbnail if image, or link if another type of file')
    )
    published = models.BooleanField(_(u"Published"), default=True)
    date_insert = models.DateTimeField(_(u"Date insert"), auto_now_add=True)
    date_update = models.DateTimeField(_(u"Date update"), auto_now=True)
    is_winner = models.BooleanField(_(u"Is winner?"), default=False)

    class Meta:
        ordering = ['-date_insert']
        verbose_name = _(u'Answer')
        verbose_name_plural = _(u'Answers')

    @property
    def filename(self):
        return os.path.basename(self.answer_file.name)

    def __unicode__(self):
        return u"{0}-{1}".format(self.promo.slug, self.answer)

    def get_file_display(self):
        try:
            imgs = ['jpg', 'png', 'jpeg', 'bmp', 'gif']
            if self.filename.split('.')[-1] in imgs:
                # return ("IMAGE:<img src=>")
                return u'<img width="100px" height="100px" src="{0}" />'.format(
                    image_url(self.answer_file.url, width=100, height=100)
                )
            else:
                return u'<a href="{0}" target="_blank">{1}</a>'.format(
                    self.answer_file.url,
                    self.filename
                )
        except:
            return _(u"No file")

    @property
    def show_file(self):
        return self.answer_file and self.publish_file
