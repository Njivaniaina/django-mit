from django import forms
from .models import User, Activity

class UserForm(forms.ModelForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'input input-primary w-full',
            'placeholder': 'Username',
            'required': True,
        })
    )

    email = forms.CharField(
        widget=forms.EmailInput(attrs={
            'class': 'input input-primary w-full',
            'placeholder': 'E-mail',
            'required': True,
        })
    )

    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'input input-primary w-full',
            'placeholder': 'Enter Password',
            'required': True,
        })
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'input input-primary w-full',
            'placeholder': 'Confirm Password',
            'required': True,
        })
    )

    image_upload = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={
            'class': 'file-input file-input-bordered w-full'
        })
    )

    image_scan = forms.CharField(
        required=False,
        widget=forms.HiddenInput()  # image encode base6
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'image_upload', 'image_scan']

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match!")

        # Fusionner image_upload et image_scan
        if not cleaned_data.get("image_upload") and not cleaned_data.get("image_scan"):
            raise forms.ValidationError("Veuillez uploader une image ou scanner votre visage.")

        return cleaned_data


class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = ['title', 'description', 'image']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'description': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full'}),
            'image': forms.ClearableFileInput(attrs={'class': 'file-input file-input-bordered w-full'}),
        }

