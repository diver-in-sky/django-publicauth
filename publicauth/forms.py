from django.utils.translation import ugettext as _
from django.contrib.auth.models import User
from django import forms

from annoying.functions import get_object_or_None
from annoying.decorators import autostrip

from publicauth.models import PublicID
from publicauth import settings


class ExtraForm(forms.Form):
    
    username = forms.CharField(min_length=3, max_length=25, label="Display Name")

    def clean_username(self):
        if get_object_or_None(User, username=self.cleaned_data['username']):
            raise forms.ValidationError(_(u'This username name is already taken'))
        return self.cleaned_data['username']

    def save(self, request, identity, provider):
        user = User.objects.create(username=self.cleaned_data['username'])
        if settings.PUBLICAUTH_ACTIVATION_REQUIRED:
            user.is_active = False
        user.save()
        PublicID.objects.create(user=user, identity=identity, provider=provider)
        return user

ExtraForm = autostrip(ExtraForm)

