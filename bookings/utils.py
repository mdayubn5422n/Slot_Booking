"""Slot maths: works out which times a customer can still book."""
from datetime import datetime, timedelta

from django.conf import settings
from django.utils import timezone

from .models import Booking


def get_available_slots(business, service, day):
    """Return a list of start times (datetime.time) that are free on `day`.

    Rules:
    - The day must be today or later, and inside the booking window.
    - The business must have working hours for that weekday.
    - A slot is as long as the service. It must fit before closing time.
    - Slots overlapping an active booking (pending/confirmed) are removed.
    - Slots that already started today are removed.
    """
    today = timezone.localdate()
    if day < today or day > today + timedelta(days=settings.BOOKING_WINDOW_DAYS):
        return []

    hours = business.hours.filter(weekday=day.weekday()).first()
    if hours is None:
        return []

    length = timedelta(minutes=service.duration_minutes)
    busy = list(
        Booking.objects.filter(business=business, date=day, status__in=[Booking.PENDING, Booking.CONFIRMED])
        .values_list("start_time", "end_time")
    )
    now_time = timezone.localtime().time()

    slots = []
    current = datetime.combine(day, hours.open_time)
    closing = datetime.combine(day, hours.close_time)
    while current + length <= closing:
        start = current.time()
        end = (current + length).time()
        already_started = day == today and start <= now_time
        overlaps = any(b_start < end and b_end > start for b_start, b_end in busy)
        if not already_started and not overlaps:
            slots.append(start)
        current += length
    return slots


def end_time_for(day, start, service):
    """Work out the end time of a booking."""
    return (datetime.combine(day, start) + timedelta(minutes=service.duration_minutes)).time()
