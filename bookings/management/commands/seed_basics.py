from django.core.management.base import BaseCommand
from django.utils.text import slugify

from bookings.models import FAQ, Category

CATEGORIES = [
    ("Salon & Barber", "Haircuts, styling and beauty"),
    ("Clinic & Dentist", "Doctor and dentist visits"),
    ("Tutor", "Lessons and coaching"),
    ("Gym & Fitness", "Training sessions and classes"),
    ("Photographer", "Photo shoots"),
    ("Pet Grooming", "Baths and grooming for pets"),
]

FAQS = [
    ("How do I book a slot?", "Open a business, press Book now, choose a service and a date, then pick a free time."),
    ("Can I cancel a booking?", "Yes. Open My bookings and press Cancel on any upcoming booking."),
    ("Do I need an account?", "Yes. A free account lets you see and manage all your bookings in one place."),
    ("How do I list my business?", "Sign up as a Business Owner, add your business, services and working hours."),
    ("Is my booking confirmed at once?", "It starts as Pending. The business owner confirms it."),
]


class Command(BaseCommand):
    help = "Adds starter categories and FAQs (no images). Safe to run many times."

    def handle(self, *args, **options):
        for name, description in CATEGORIES:
            Category.objects.get_or_create(slug=slugify(name), defaults={"name": name, "description": description})
        for order, (question, answer) in enumerate(FAQS):
            FAQ.objects.get_or_create(question=question, defaults={"answer": answer, "order": order})
        self.stdout.write(self.style.SUCCESS("Starter categories and FAQs added."))
