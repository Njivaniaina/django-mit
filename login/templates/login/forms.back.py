from django import forms
from .models import User

class UserForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'input input-primary w-full',
            'placeholder': 'Password'
        })
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'input input-primary w-full',
            'placeholder': 'Confirm Password'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'image']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'input input-primary w-full',
                'placeholder': 'Username'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'input input-primary w-full',
                'placeholder': 'E-mail'
            }),
            'image': forms.FileInput(attrs={
                'class': 'file-input file-inpurt-primary file-input-bordered w-full'
            }),
        }

    # Verify the pass word
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Les mots de passe ne correspondent pas ❌")

        return cleaned_data

