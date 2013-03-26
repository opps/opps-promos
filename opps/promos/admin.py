# -*- coding: utf-8 -*-
from django.contrib import admin
from django import forms
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.utils.translation import ugettext_lazy as _

from redactor.widgets import RedactorEditor