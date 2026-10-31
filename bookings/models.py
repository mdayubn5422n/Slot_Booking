import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify


def validate_image_size(image):
    """Reject images bigger than 5 MB."""
    if image.size > 5 * 1024 * 1024:
        raise ValidationError("Image is too large. Please upload a file under 5 MB.")


class Category(models.Model):
    """A type of business, e.g. Salon, Clinic. The Platform Admin adds these."""

    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(unique=True)
    description = models.CharField(max_length=200, blank=True)
    image = models.ImageField(upload_to="categories/", blank=True, validators=[validate_image_size])

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Business(models.Model):
    """A small business that takes bookings. Owned by a Business Owner."""

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="businesses")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="businesses")
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    address = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    image = models.ImageField(upload_to="businesses/", blank=True, validators=[validate_image_size])
    is_active = models.BooleanField(default=True, help_text="Untick to hide this business from customers.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "businesses"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Make a unique web-friendly name (slug) the first time we save.
        if not self.slug:
            base = slugify(self.name) or "business"
            slug, n = base, 2
            while Business.objects.filter(slug=slug).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)


class Service(models.Model):
    """Something a business offers, e.g. Haircut (30 minutes, 500)."""

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="services")
    name = models.CharField(max_length=100)
    duration_minutes = models.PositiveSmallIntegerField(default=30, help_text="How long one booking lasts, in minutes.")
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.business.name})"

    def clean(self):
        if self.duration_minutes < 5:
            raise ValidationError("Duration must be at least 5 minutes.")


class WorkingHours(models.Model):
    """Opening hours for one weekday. Bookable slots are made from these."""

    WEEKDAYS = [(0, "Monday"), (1, "Tuesday"), (2, "Wednesday"), (3, "Thursday"),
                (4, "Friday"), (5, "Saturday"), (6, "Sunday")]

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="hours")
    weekday = models.PositiveSmallIntegerField(choices=WEEKDAYS)
    open_time = models.TimeField()
    close_time = models.TimeField()

    class Meta:
        ordering = ["weekday"]
        unique_together = ("business", "weekday")
        verbose_name_plural = "working hours"

    def __str__(self):
        return f"{self.business.name}: {self.get_weekday_display()} {self.open_time:%H:%M}-{self.close_time:%H:%M}"

    def clean(self):
        if self.open_time and self.close_time and self.close_time <= self.open_time:
            raise ValidationError("Closing time must be after opening time.")


class Booking(models.Model):
    """One customer booking one time slot."""

    PENDING, CONFIRMED, CANCELLED, COMPLETED = "pending", "confirmed", "cancelled", "completed"
    STATUS_CHOICES = [(PENDING, "Pending"), (CONFIRMED, "Confirmed"),
                      (CANCELLED, "Cancelled"), (COMPLETED, "Completed")]

    reference = models.CharField(max_length=10, unique=True, editable=False)
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookings")
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="bookings")
    service = models.ForeignKey(Service, on_delete=models.PROTECT, related_name="bookings")
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    note = models.CharField(max_length=300, blank=True)
    # UTM tracking: where did this customer come from?
    utm_source = models.CharField(max_length=100, blank=True)
    utm_medium = models.CharField(max_length=100, blank=True)
    utm_campaign = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date", "start_time"]

    def __str__(self):
        return f"{self.reference} - {self.business.name} {self.date} {self.start_time:%H:%M}"

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = uuid.uuid4().hex[:8].upper()
        super().save(*args, **kwargs)

    @property
    def is_active(self):
        """Pending or confirmed bookings block the slot."""
        return self.status in (self.PENDING, self.CONFIRMED)


class SiteImage(models.Model):
    """Images for the home page and other fixed places. Added by the Platform Admin."""

    HOME_HERO, HOME_ABOUT, CONTACT = "home_hero", "home_about", "contact"
    KEY_CHOICES = [(HOME_HERO, "Home page - main banner"), (HOME_ABOUT, "Home page - about section"),
                   (CONTACT, "Contact page image")]

    key = models.CharField(max_length=20, choices=KEY_CHOICES, unique=True)
    image = models.ImageField(upload_to="site/", validators=[validate_image_size])
    alt_text = models.CharField(max_length=150, blank=True, help_text="Short description for screen readers.")

    def __str__(self):
        return self.get_key_display()


class FAQ(models.Model):
    """Question and answer shown in the expandable FAQ on the home page."""

    question = models.CharField(max_length=200)
    answer = models.TextField()
    order = models.PositiveSmallIntegerField(default=0)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self):
        return self.question


class ContactMessage(models.Model):
    """A message sent from the contact page."""

    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    utm_source = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.created_at:%Y-%m-%d})"
