from django.contrib.auth.forms import UserCreationForm
from django import forms
from .models import CustomUser

class SignupForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model   = CustomUser
        fields  = ("username","email", )

class UpdateUserForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ("username", "first_name", "last_name", "first_name_kana", "last_name_kana", "phone_number", "age")