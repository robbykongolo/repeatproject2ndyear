from django import forms


class VoucherApplyForm(forms.Form):
    code = forms.CharField(
        label="Code",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter code"})
    )
