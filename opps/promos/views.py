#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from opps.channels.models import Channel

from .utils import CookedResponse