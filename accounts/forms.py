from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import Profile

User = get_user_model()


class SignupForm(UserCreationForm):
    """Sign-up form: username, email, phone, role and password."""

    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=20, required=False)
    role = forms.ChoiceField(choices=Profile.ROLE_CHOICES, initial=Profile.CUSTOMER)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.save()
        # Create the profile that stores the role.
        Profile.objects.create(user=user, role=self.cleaned_data["role"], phone=self.cleaned_data["phone"])
        return user
