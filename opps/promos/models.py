# -*- coding: utf-8 -*-
from django.db import models
from django.db.models import Sum
from django.utils import timezone
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from tagging.fields import TagField

from opps.core.models import Publishable
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

    tags = TagField(null=True, verbose_name=_(u"Tags"))
    date_end = models.DateTimeField(_(u"End date"), null=True, blank=True)
    position  = models.IntegerField(_(u"Position"), default=0)
    template_path  = models.CharField(_(u"Template Path"), blank=True,
                                     null=True, max_length=255)

    has_upload = models.BooleanField(_(u"Has file upload?"), default=False)
    has_urlfield = models.BooleanField(_(u"Has url field?"), default=False)

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
    filename = "{0}-{1}.{2}".format(uuid.uuid4(), instance.slug, ext)
    d = datetime.now()
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