from django import forms

from .models import Council, Profile


class RegistrationForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    name = forms.CharField(max_length=150)
    category = forms.ChoiceField(choices=Profile._meta.get_field("category").choices or [])


class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["name", "phone", "biography", "notifications_enabled"]
        help_texts = {
            "biography": "User-provided, unverified. This is not a verified professional credential."
        }


class CodeForm(forms.Form):
    code = forms.RegexField(r"^[0-9]{6}$", max_length=6)


class EmailForm(forms.Form):
    email = forms.EmailField()


class ConfirmationForm(CodeForm):
    email = forms.EmailField()


class ResetForm(ConfirmationForm):
    password = forms.CharField(widget=forms.PasswordInput)


class SubmissionForm(forms.Form):
    category = forms.ChoiceField(choices=Profile._meta.get_field("category").choices or [])
    council = forms.ModelChoiceField(queryset=Council.objects.filter(active=True), required=False)
    registration_number = forms.CharField(max_length=100, required=False)
    card = forms.FileField(required=False)


class ReviewForm(forms.Form):
    action = forms.ChoiceField(
        choices=[
            (x, x.title()) for x in ["review", "approve", "return", "reject", "revoke", "update"]
        ]
    )
    version = forms.IntegerField(widget=forms.HiddenInput)
    reason = forms.CharField(widget=forms.Textarea)
    registered_name = forms.CharField(max_length=150, required=False)
    council = forms.ModelChoiceField(queryset=Council.objects.filter(active=True), required=False)
    registration_number = forms.CharField(max_length=100, required=False)
    profession = forms.CharField(max_length=150, required=False)
    programme = forms.CharField(max_length=200, required=False)
    school = forms.CharField(max_length=200, required=False)
