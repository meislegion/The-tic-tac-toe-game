# -*- coding: utf-8 -*-
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.db import IntegrityError, transaction
from django.utils.translation import ugettext as _


class RegForm(forms.Form):
    name = forms.CharField(label=_(u'Имя'), max_length=20, widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label=_(u'Пароль'), max_length=20, widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    def user_exist(self):
        if self.is_valid():
            try:
                User.objects.get(username=self.cleaned_data['name'])
                return True
            except User.DoesNotExist:
                return False
        raise forms.ValidationError(_(u'Введите имя пользователя и пароль'))

    def user_login(self):
        if self.user_exist():
            user = authenticate(username=self.cleaned_data['name'], password=self.cleaned_data['password'])
            if user is not None:
                if user.is_active:
                    return None
                else:
                    raise forms.ValidationError(_(u'Пользователь заблокирован'))

        raise forms.ValidationError(_(u'Неправильное имя пользователя или пароль'))

    def user_registration(self):
        if not self.user_exist():
            try:
                with transaction.atomic():
                    new_user = User.objects.create_user(username=self.cleaned_data['name'],
                                                        password=self.cleaned_data['password'])
                    new_user.save()
                return None
            except IntegrityError:
                raise forms.ValidationError(_(u'Данное имя пользователя занято, введите другое имя'))

        raise forms.ValidationError(_(u'Данное имя пользователя занято, введите другое имя'))
