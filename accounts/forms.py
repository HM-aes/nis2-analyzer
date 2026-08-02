from django import forms
from django.contrib.auth.models import User


class SignupForm(forms.Form):
    email = forms.EmailField()
    organisation = forms.CharField(max_length=200)
    password1 = forms.CharField(widget=forms.PasswordInput, min_length=10)

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(username=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean_password1(self):
        password = self.cleaned_data["password1"]
        if len(password) < 10:
            raise forms.ValidationError("Password must be at least 10 characters.")
        return password

    def save(self):
        email = self.cleaned_data["email"]
        return User.objects.create_user(
            username=email,
            email=email,
            password=self.cleaned_data["password1"],
            first_name=self.cleaned_data["organisation"],
        )


class LoginForm(forms.Form):
    email = forms.CharField(label="Email or username")
    password = forms.CharField(widget=forms.PasswordInput)
