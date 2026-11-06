from django import forms

from .models import Profile


class RegistrationForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    name = forms.CharField(max_length=150)
    role = forms.ChoiceField(choices=[("learner", "Learner"), ("trainer", "Trainer")])


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["name", "phone", "biography", "notifications_enabled"]


class CodeForm(forms.Form):
    code = forms.RegexField(r"^[0-9]{5}$")
