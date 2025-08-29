from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Order


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text="Required. Enter a valid email address.")

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class ShippingForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["full_name", "address1", "address2", "city", "county", "postcode", "country", "phone"]
        widgets = {
            "full_name": forms.TextInput(attrs={"class":"form-control"}),
            "address1":  forms.TextInput(attrs={"class":"form-control"}),
            "address2":  forms.TextInput(attrs={"class":"form-control"}),
            "city":      forms.TextInput(attrs={"class":"form-control"}),
            "county":    forms.TextInput(attrs={"class":"form-control"}),
            "postcode":  forms.TextInput(attrs={"class":"form-control"}),
            "country":   forms.TextInput(attrs={"class":"form-control", "placeholder":"IE"}),
            "phone":     forms.TextInput(attrs={"class":"form-control"}),
        }
        labels = {"county":"County / State / Region", "postcode":"Postcode / ZIP"}
