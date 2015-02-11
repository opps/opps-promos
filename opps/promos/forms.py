# -*- coding: utf-8 -*-

from django import forms
from django.utils.translation import ugettext_lazy as _

from .models import Answer


class BaseAnswerForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(BaseAnswerForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            if field in self._meta.fields:
                self.fields[field].required = True

    agree = forms.BooleanField(
        label=_(u"I agree with terms."), initial=False, required=False)

    def clean(self):
        cleaned_data = super(BaseAnswerForm, self).clean()
        if not cleaned_data.get('agree'):
            raise forms.ValidationError(_(u"You have to agree with the rules"))
        return cleaned_data

    class Meta:
        model = Answer
        fields = ('answer', 'answer_url', 'answer_file',)


class AnonyUserForm(forms.Form):
    name = forms.CharField(label=_('name'), max_length=200)
    birthday = forms.DateField(label=_('birthday'))
    email = forms.EmailField(label=_("e-mail"))
