from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Profile, is_owner

User = get_user_model()


class SignupTests(TestCase):
    def post_signup(self, role):
        return self.client.post(reverse("accounts:signup"), {
            "username": "sam", "email": "sam@example.com", "phone": "123",
            "role": role, "password1": "StrongPass#2026", "password2": "StrongPass#2026",
        })

    def test_customer_signup_creates_profile(self):
        self.post_signup("customer")
        user = User.objects.get(username="sam")
        self.assertEqual(user.profile.role, Profile.CUSTOMER)
        self.assertFalse(is_owner(user))

    def test_owner_signup_goes_to_dashboard(self):
        response = self.post_signup("owner")
        self.assertRedirects(response, reverse("owner_dashboard"))
        self.assertTrue(is_owner(User.objects.get(username="sam")))

    def test_password_mismatch_shows_error(self):
        response = self.client.post(reverse("accounts:signup"), {
            "username": "sam", "email": "a@b.com", "role": "customer",
            "password1": "StrongPass#2026", "password2": "different",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="sam").exists())

    def test_login_page_loads(self):
        self.assertEqual(self.client.get(reverse("accounts:login")).status_code, 200)
