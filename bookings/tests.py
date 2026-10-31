from datetime import time, timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Profile

from .models import Booking, Business, Category, ContactMessage, Service, WorkingHours
from .utils import end_time_for, get_available_slots

User = get_user_model()


class BaseTestCase(TestCase):
    """Creates an owner, a customer, a business with one 30-minute service and hours 09:00-12:00 every day."""

    def setUp(self):
        self.owner = User.objects.create_user("owner1", password="pass12345")
        Profile.objects.create(user=self.owner, role=Profile.OWNER)
        self.other_owner = User.objects.create_user("owner2", password="pass12345")
        Profile.objects.create(user=self.other_owner, role=Profile.OWNER)
        self.customer = User.objects.create_user("cust1", password="pass12345")
        Profile.objects.create(user=self.customer, role=Profile.CUSTOMER)
        self.customer2 = User.objects.create_user("cust2", password="pass12345")
        Profile.objects.create(user=self.customer2, role=Profile.CUSTOMER)

        self.category = Category.objects.create(name="Salon", slug="salon")
        self.business = Business.objects.create(owner=self.owner, category=self.category, name="Test Salon")
        self.service = Service.objects.create(business=self.business, name="Haircut", duration_minutes=30, price=100)
        for weekday in range(7):
            WorkingHours.objects.create(business=self.business, weekday=weekday,
                                        open_time=time(9, 0), close_time=time(12, 0))
        self.tomorrow = timezone.localdate() + timedelta(days=1)

    def make_booking(self, user=None, start=time(9, 0), status=Booking.PENDING):
        return Booking.objects.create(
            customer=user or self.customer, business=self.business, service=self.service, date=self.tomorrow,
            start_time=start, end_time=end_time_for(self.tomorrow, start, self.service), status=status)


class SlotTests(BaseTestCase):
    def test_slots_are_made_from_working_hours(self):
        slots = get_available_slots(self.business, self.service, self.tomorrow)
        self.assertEqual(len(slots), 6)  # 09:00 ... 11:30
        self.assertEqual(slots[0], time(9, 0))
        self.assertEqual(slots[-1], time(11, 30))

    def test_booked_slot_is_removed(self):
        self.make_booking(start=time(9, 0))
        self.assertNotIn(time(9, 0), get_available_slots(self.business, self.service, self.tomorrow))

    def test_cancelled_slot_is_free_again(self):
        self.make_booking(start=time(9, 0), status=Booking.CANCELLED)
        self.assertIn(time(9, 0), get_available_slots(self.business, self.service, self.tomorrow))

    def test_past_date_has_no_slots(self):
        yesterday = timezone.localdate() - timedelta(days=1)
        self.assertEqual(get_available_slots(self.business, self.service, yesterday), [])

    def test_day_without_hours_has_no_slots(self):
        WorkingHours.objects.filter(business=self.business, weekday=self.tomorrow.weekday()).delete()
        self.assertEqual(get_available_slots(self.business, self.service, self.tomorrow), [])

    def test_far_future_date_has_no_slots(self):
        far = timezone.localdate() + timedelta(days=500)
        self.assertEqual(get_available_slots(self.business, self.service, far), [])

    def test_long_service_blocks_overlapping_slots(self):
        long_service = Service.objects.create(business=self.business, name="Colour", duration_minutes=60, price=300)
        self.make_booking(start=time(9, 30))  # busy 09:30-10:00
        slots = get_available_slots(self.business, long_service, self.tomorrow)
        self.assertNotIn(time(9, 0), slots)   # 09:00-10:00 overlaps
        self.assertIn(time(10, 0), slots)


class ModelTests(BaseTestCase):
    def test_business_slug_is_unique(self):
        second = Business.objects.create(owner=self.owner, category=self.category, name="Test Salon")
        self.assertNotEqual(second.slug, self.business.slug)

    def test_booking_gets_reference(self):
        self.assertEqual(len(self.make_booking().reference), 8)

    def test_working_hours_validation(self):
        hours = WorkingHours(business=self.business, weekday=1, open_time=time(10, 0), close_time=time(9, 0))
        with self.assertRaises(ValidationError):
            hours.clean()


class BookingFlowTests(BaseTestCase):
    def post_booking(self, slot="09:00"):
        return self.client.post(reverse("book", args=[self.business.slug]), {
            "service": self.service.pk, "date": self.tomorrow.isoformat(), "slot": slot, "note": "Hi"})

    def test_login_required_to_book(self):
        response = self.client.get(reverse("book", args=[self.business.slug]))
        self.assertEqual(response.status_code, 302)

    def test_customer_can_book(self):
        self.client.login(username="cust1", password="pass12345")
        response = self.post_booking()
        booking = Booking.objects.get()
        self.assertRedirects(response, reverse("booking_detail", args=[booking.reference]))
        self.assertEqual(booking.start_time, time(9, 0))
        self.assertEqual(booking.end_time, time(9, 30))

    def test_double_booking_is_blocked(self):
        self.client.login(username="cust1", password="pass12345")
        self.post_booking()
        self.client.logout()
        self.client.login(username="cust2", password="pass12345")
        self.post_booking()
        self.assertEqual(Booking.objects.count(), 1)

    def test_owner_cannot_book(self):
        self.client.login(username="owner1", password="pass12345")
        self.post_booking()
        self.assertEqual(Booking.objects.count(), 0)

    def test_invalid_slot_is_rejected(self):
        self.client.login(username="cust1", password="pass12345")
        self.post_booking(slot="03:00")
        self.assertEqual(Booking.objects.count(), 0)

    def test_utm_values_are_saved(self):
        self.client.login(username="cust1", password="pass12345")
        self.client.get(reverse("home") + "?utm_source=newsletter&utm_medium=email")
        self.post_booking()
        self.assertEqual(Booking.objects.get().utm_source, "newsletter")

    def test_customer_can_cancel_own_booking(self):
        booking = self.make_booking()
        self.client.login(username="cust1", password="pass12345")
        self.client.post(reverse("cancel_booking", args=[booking.reference]))
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.CANCELLED)

    def test_customer_cannot_cancel_someone_elses_booking(self):
        booking = self.make_booking()
        self.client.login(username="cust2", password="pass12345")
        response = self.client.post(reverse("cancel_booking", args=[booking.reference]))
        self.assertEqual(response.status_code, 404)

    def test_booking_detail_is_private(self):
        booking = self.make_booking()
        self.client.login(username="cust2", password="pass12345")
        self.assertEqual(self.client.get(reverse("booking_detail", args=[booking.reference])).status_code, 403)
        self.client.login(username="cust1", password="pass12345")
        self.assertEqual(self.client.get(reverse("booking_detail", args=[booking.reference])).status_code, 200)

    def test_my_bookings_page(self):
        self.make_booking()
        self.client.login(username="cust1", password="pass12345")
        self.assertContains(self.client.get(reverse("my_bookings")), "Test Salon")


class OwnerTests(BaseTestCase):
    def test_customer_cannot_open_owner_dashboard(self):
        self.client.login(username="cust1", password="pass12345")
        self.assertEqual(self.client.get(reverse("owner_dashboard")).status_code, 403)

    def test_owner_can_open_dashboard_and_manage(self):
        self.client.login(username="owner1", password="pass12345")
        self.assertEqual(self.client.get(reverse("owner_dashboard")).status_code, 200)
        self.assertEqual(self.client.get(reverse("manage", args=[self.business.slug])).status_code, 200)

    def test_other_owner_cannot_manage_business(self):
        self.client.login(username="owner2", password="pass12345")
        self.assertEqual(self.client.get(reverse("manage", args=[self.business.slug])).status_code, 404)

    def test_owner_confirms_and_completes_booking(self):
        booking = self.make_booking()
        self.client.login(username="owner1", password="pass12345")
        url = reverse("booking_status", args=[booking.reference])
        self.client.post(url, {"action": "confirm"})
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.CONFIRMED)
        self.client.post(url, {"action": "complete"})
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.COMPLETED)

    def test_other_owner_cannot_change_booking(self):
        booking = self.make_booking()
        self.client.login(username="owner2", password="pass12345")
        response = self.client.post(reverse("booking_status", args=[booking.reference]), {"action": "confirm"})
        self.assertEqual(response.status_code, 404)

    def test_owner_adds_service_and_hours(self):
        self.client.login(username="owner1", password="pass12345")
        self.client.post(reverse("service_add", args=[self.business.slug]),
                         {"name": "Shave", "duration_minutes": 15, "price": "50"})
        self.assertTrue(Service.objects.filter(name="Shave").exists())
        self.client.post(reverse("hours_add", args=[self.business.slug]),
                         {"weekday": 0, "open_time": "08:00", "close_time": "10:00"})
        self.assertEqual(WorkingHours.objects.get(business=self.business, weekday=0).open_time, time(8, 0))

    def test_service_with_bookings_cannot_be_deleted(self):
        self.make_booking()
        self.client.login(username="owner1", password="pass12345")
        self.client.post(reverse("service_delete", args=[self.service.pk]))
        self.assertTrue(Service.objects.filter(pk=self.service.pk).exists())

    def test_owner_creates_business(self):
        self.client.login(username="owner1", password="pass12345")
        self.client.post(reverse("business_create"), {"category": self.category.pk, "name": "New Place", "is_active": "on"})
        self.assertTrue(Business.objects.filter(name="New Place", owner=self.owner).exists())


class PublicPageTests(BaseTestCase):
    def test_public_pages_load(self):
        for name in ("home", "business_list", "contact"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)
        self.assertEqual(self.client.get(reverse("business_detail", args=[self.business.slug])).status_code, 200)

    def test_search_finds_business(self):
        response = self.client.get(reverse("business_list"), {"q": "Test Salon"})
        self.assertContains(response, "Test Salon")
        response = self.client.get(reverse("business_list"), {"q": "zzzz"})
        self.assertNotContains(response, "Test Salon")

    def test_inactive_business_is_hidden(self):
        self.business.is_active = False
        self.business.save()
        self.assertEqual(self.client.get(reverse("business_detail", args=[self.business.slug])).status_code, 404)

    def test_contact_form_saves_message(self):
        self.client.post(reverse("contact"), {"name": "Sam", "email": "s@example.com", "message": "Hello"})
        self.assertEqual(ContactMessage.objects.count(), 1)

    def test_contact_form_error(self):
        response = self.client.post(reverse("contact"), {"name": "", "email": "bad", "message": ""})
        self.assertContains(response, "errorlist")
