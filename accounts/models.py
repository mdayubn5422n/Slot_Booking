from django.conf import settings
from django.db import models


class Profile(models.Model):
    """Extra information for each user: are they a customer or a business owner?
    (Platform Admins are Django superusers and use /admin/.)"""

    CUSTOMER = "customer"
    OWNER = "owner"
    ROLE_CHOICES = [(CUSTOMER, "Customer"), (OWNER, "Business Owner")]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=CUSTOMER)
    phone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"


def is_owner(user):
    """True if this user is a Business Owner."""
    if not user.is_authenticated:
        return False
    profile = getattr(user, "profile", None)  # None when the user has no profile
    return bool(profile and profile.role == Profile.OWNER)
