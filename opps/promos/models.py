# -*- coding: utf-8 -*-

import os
import uuid

from django.db import models
from django.db.models import Sum
from django.utils import timezone
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError

from taggit.managers import TaggableManager

from opps.core.models import Publishable, BaseBox, BaseConfig
from opps.channels.models import Channel
from opps.articles.models import Post
from opps.images.models import Image


class Promo(Publishable):
    title = models.CharField(_(u"Title"), max_length=255)
    slug = models.SlugField(_(u"URL"), max_length=150, unique=True,
                            db_index=True)

    headline = models.TextField(_(u"Headline"), blank=True)
    description = models.TextField(_(u"Description"), blank=True)

    rules = models.TextField(_(u'Rules'), blank=True)
    result = models.TextField(_(u'Result'), blank=True)

    channel = models.ForeignKey(Channel, null=True, blank=True,
                                on_delete=models.SET_NULL)
    posts = models.ManyToManyField(Post, null=True, blank=True,
                                   related_name='promo_post',
                                   through='PromoPost')

    main_image = models.ForeignKey(Image,
                                   verbose_name=_(u'Promo Image'), blank=True,
                                   null=True, on_delete=models.SET_NULL,
                                   related_name='promo_image')

    tags = TaggableManager(blank=True)
    date_end = models.DateTimeField(_(u"End date"), null=True, blank=True)
    position  = models.IntegerField(_(u"Position"), default=0)

    has_upload = models.BooleanField(_(u"Has file upload?"), default=False)
    has_urlfield = models.BooleanField(_(u"Has url field?"), default=False)

    display_answers = models.BooleanField(_(u"Display answers?"), default=True)
    display_winners = models.BooleanField(_(u"Display winners?"), default=False)


    send_confirmation_email = models.BooleanField(_(u"Send confirmation email?"),
            default=False)

    confirmation_email_txt = models.TextField(_(u'Confirmation email (Text)'),
            blank=True)
    confirmation_email_html = models.TextField(_(u'Confirmation email (HTML)'),
            blank=True)
    confirmation_email_address = models.EmailField(_(u'Email'), max_length=255,
            null=True, blank=True)

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

    class Meta:
        ordering = ['position']


class PromoPost(models.Model):
    post = models.ForeignKey(Post, verbose_name=_(u'Promo Post'), null=True,
                             blank=True, related_name='promopost_post',
                             on_delete=models.SET_NULL)
    promo = models.ForeignKey(Promo, verbose_name=_(u'Promo'), null=True,
                                   blank=True, related_name='promo',
                                   on_delete=models.SET_NULL)


    def __unicode__(self):
        return u"{0}-{1}".format(self.promo.slug, self.post.slug)


def get_file_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = "{0}-{1}.{2}".format(uuid.uuid4(), instance.promo.slug, ext)
    d = timezone.now()
    folder = "promos/{0}".format(d.strftime("%Y/%m/%d/"))
    return os.path.join(folder, filename)


class Answer(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    promo = models.ForeignKey(Promo)
    answer = models.TextField(_(u"Answer"), blank=True, null=True)
    answer_url = models.URLField(_(u"Answer URL"), blank=True, null=True)
    answer_file = models.FileField(upload_to=get_file_path, blank=True, null=True)
    published = models.BooleanField(_(u"Published"), default=True)
    date_insert = models.DateTimeField(_(u"Date insert"), auto_now_add=True)
    date_update = models.DateTimeField(_(u"Date update"), auto_now=True)
    is_winner = models.BooleanField(_(u"Is winner?"), default=False)

    class Meta:
        ordering = ['-date_insert']

    def __unicode__(self):
        return u"{0}-{1}".format(self.promo.slug, self.answer)


class PromoBox(BaseBox):

    promos = models.ManyToManyField(
        'promos.Promo',
        null=True, blank=True,
        related_name='promobox_promos',
        through='promos.PromoBoxPromos'
    )


class PromoBoxPromos(models.Model):
    promobox = models.ForeignKey(
        'promos.PromoBox',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='promoboxpromos_promoboxes',
        verbose_name=_(u'Promo Box'),
    )
    promo = models.ForeignKey(
        'promos.Promo',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='promoboxpromos_promos',
        verbose_name=_(u'Promo'),
    )
    order = models.PositiveIntegerField(_(u'Order'), default=0)

    def __unicode__(self):
        return u"{0}-{1}".format(self.promobox.slug, self.promo.slug)

    def clean(self):

        if not self.promo.published:
            raise ValidationError('Promo not published!')

        if self.promo.date_available <= timezone.now():
            raise ValidationError('Promo not published!')


class PromoConfig(BaseConfig):

    promo = models.ForeignKey(
        'promos.Promo',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='promoconfig_promos',
        verbose_name=_(u'Promo'),
    )

    class Meta:
        permissions = (("developer", "Developer"),)
        unique_together = ("key_group", "key", "site", "channel", "article", "promo")

