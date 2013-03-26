# -*- coding: utf-8 -*-
from django.db import models
from django.db.models import Sum
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from tagging.fields import TagField

from opps.core.models import Publishable
from opps.channels.models import Channel
from opps.articles.models import Post
from opps.images.models import Image