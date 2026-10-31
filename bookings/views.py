from datetime import date, timedelta
from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import is_owner

from .forms import BusinessForm, ContactForm, ServiceForm, WorkingHoursForm
from .models import FAQ, Booking, Business, Category, Service, SiteImage, WorkingHours
from .utils import end_time_for, get_available_slots


def owner_required(view):
    """Only logged-in Business Owners may open the page."""

    @wraps(view)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not is_owner(request.user):
            raise PermissionDenied
        return view(request, *args, **kwargs)

    return wrapper


# ------------------------------------------------------------------ public pages
def home(request):
    context = {
        "categories": Category.objects.all(),
        "featured": Business.objects.filter(is_active=True).select_related("category")[:6],
        "faqs": FAQ.objects.filter(is_published=True),
        "images": {i.key: i for i in SiteImage.objects.all()},
    }
    return render(request, "bookings/home.html", context)


def business_list(request):
    """Business list with site search (?q=) and category filter (?category=)."""
    businesses = Business.objects.filter(is_active=True).select_related("category")
    query = request.GET.get("q", "").strip()
    category_slug = request.GET.get("category", "")
    if query:
        businesses = businesses.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
            | Q(address__icontains=query) | Q(category__name__icontains=query)
        )
    if category_slug:
        businesses = businesses.filter(category__slug=category_slug)
    page = Paginator(businesses, 9).get_page(request.GET.get("page"))
    context = {"page": page, "query": query, "category_slug": category_slug, "categories": Category.objects.all()}
    return render(request, "bookings/business_list.html", context)


def business_detail(request, slug):
    business = get_object_or_404(Business, slug=slug, is_active=True)
    context = {"business": business, "services": business.services.all(), "hours": business.hours.all()}
    return render(request, "bookings/business_detail.html", context)


def contact(request):
    form = ContactForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        message = form.save(commit=False)
        message.utm_source = request.session.get("utm", {}).get("utm_source", "")
        message.save()
        messages.success(request, "Thank you! Your message was sent. We will reply soon.")
        return redirect("contact")
    images = {i.key: i for i in SiteImage.objects.all()}
    return render(request, "bookings/contact.html", {"form": form, "images": images})


# ------------------------------------------------------------------ customer pages
@login_required
def book(request, slug):
    """Step 1: choose service and date (GET). Step 2: choose a free time and confirm (POST)."""
    business = get_object_or_404(Business, slug=slug, is_active=True)
    if is_owner(request.user):
        messages.error(request, "Business Owner accounts cannot make bookings. Please use a customer account.")
        return redirect("business_detail", slug=slug)

    services = business.services.all()
    data = request.POST if request.method == "POST" else request.GET

    # Read the chosen service and date safely.
    service = None
    service_id = data.get("service", "")
    if service_id.isdigit():
        service = services.filter(pk=int(service_id)).first()
    day = None
    try:
        day = date.fromisoformat(data.get("date", ""))
    except ValueError:
        pass

    slots = get_available_slots(business, service, day) if service and day else []

    if request.method == "POST":
        chosen = data.get("slot", "")
        if not (service and day):
            messages.error(request, "Please choose a service and a date.")
        else:
            with transaction.atomic():
                # Check again inside the transaction so two people cannot take the same slot.
                free = get_available_slots(business, service, day)
                start = next((s for s in free if s.strftime("%H:%M") == chosen), None)
                if start is None:
                    messages.error(request, "Sorry, that time is not available any more. Please pick another.")
                else:
                    utm = request.session.get("utm", {})
                    booking = Booking.objects.create(
                        customer=request.user, business=business, service=service, date=day,
                        start_time=start, end_time=end_time_for(day, start, service),
                        note=data.get("note", "")[:300],
                        utm_source=utm.get("utm_source", ""), utm_medium=utm.get("utm_medium", ""),
                        utm_campaign=utm.get("utm_campaign", ""),
                    )
                    messages.success(request, "Booking received! The business will confirm it soon.")
                    return redirect("booking_detail", reference=booking.reference)

    today = timezone.localdate()
    context = {
        "business": business, "services": services, "service": service, "day": day, "slots": slots,
        "min_date": today, "max_date": today + timedelta(days=settings.BOOKING_WINDOW_DAYS),
        "searched": bool(service and day),
    }
    return render(request, "bookings/book.html", context)


@login_required
def booking_detail(request, reference):
    """Confirmation page. Printable. Visible to the customer, the business owner and staff."""
    booking = get_object_or_404(Booking.objects.select_related("business", "service"), reference=reference)
    allowed = (request.user == booking.customer or request.user == booking.business.owner
               or request.user.is_staff)
    if not allowed:
        raise PermissionDenied
    return render(request, "bookings/booking_detail.html", {"booking": booking})


@login_required
def my_bookings(request):
    today = timezone.localdate()
    mine = Booking.objects.filter(customer=request.user).select_related("business", "service")
    upcoming = mine.filter(date__gte=today).exclude(status__in=[Booking.CANCELLED, Booking.COMPLETED])
    past = mine.exclude(pk__in=upcoming.values("pk")).order_by("-date", "-start_time")
    return render(request, "bookings/my_bookings.html", {"upcoming": upcoming, "past": past})


@login_required
@require_POST
def cancel_booking(request, reference):
    booking = get_object_or_404(Booking, reference=reference, customer=request.user)
    if booking.is_active and booking.date >= timezone.localdate():
        booking.status = Booking.CANCELLED
        booking.save(update_fields=["status"])
        messages.success(request, "Your booking was cancelled.")
    else:
        messages.error(request, "This booking can not be cancelled.")
    return redirect("my_bookings")


# ------------------------------------------------------------------ business owner pages
def get_own_business(request, slug):
    """Find a business, but only if it belongs to the logged-in owner."""
    return get_object_or_404(Business, slug=slug, owner=request.user)


@owner_required
def owner_dashboard(request):
    businesses = request.user.businesses.annotate(
        pending=Count("bookings", filter=Q(bookings__status=Booking.PENDING))
    )
    return render(request, "owner/dashboard.html", {"businesses": businesses})


@owner_required
def business_form(request, slug=None):
    """Create a new business (slug is None) or edit an existing one."""
    business = get_own_business(request, slug) if slug else None
    form = BusinessForm(request.POST or None, request.FILES or None, instance=business)
    if request.method == "POST" and form.is_valid():
        saved = form.save(commit=False)
        saved.owner = request.user
        saved.save()
        messages.success(request, "Business saved.")
        return redirect("manage", slug=saved.slug)
    return render(request, "owner/business_form.html", {"form": form, "business": business})


@owner_required
def manage(request, slug):
    """One page to manage services, working hours and bookings of a business."""
    business = get_own_business(request, slug)
    status = request.GET.get("status", "")
    bookings = business.bookings.select_related("customer", "service").order_by("-date", "-start_time")
    if status in dict(Booking.STATUS_CHOICES):
        bookings = bookings.filter(status=status)
    context = {
        "business": business, "services": business.services.all(), "hours": business.hours.all(),
        "bookings": bookings, "status": status, "statuses": Booking.STATUS_CHOICES,
        "service_form": ServiceForm(), "hours_form": WorkingHoursForm(),
    }
    return render(request, "owner/manage.html", context)


@owner_required
@require_POST
def service_add(request, slug):
    business = get_own_business(request, slug)
    form = ServiceForm(request.POST)
    if form.is_valid():
        service = form.save(commit=False)
        service.business = business
        service.save()
        messages.success(request, "Service added.")
    else:
        messages.error(request, "Could not add the service: " + "; ".join(
            e for errs in form.errors.values() for e in errs))
    return redirect("manage", slug=slug)


@owner_required
@require_POST
def service_delete(request, pk):
    service = get_object_or_404(Service, pk=pk, business__owner=request.user)
    slug = service.business.slug
    if service.bookings.exists():
        messages.error(request, "This service already has bookings, so it can not be deleted.")
    else:
        service.delete()
        messages.success(request, "Service deleted.")
    return redirect("manage", slug=slug)


@owner_required
@require_POST
def hours_add(request, slug):
    """Add or replace the opening hours of one weekday."""
    business = get_own_business(request, slug)
    form = WorkingHoursForm(request.POST)
    if form.is_valid():
        data = form.cleaned_data
        if data["close_time"] <= data["open_time"]:
            messages.error(request, "Closing time must be after opening time.")
        else:
            WorkingHours.objects.update_or_create(
                business=business, weekday=data["weekday"],
                defaults={"open_time": data["open_time"], "close_time": data["close_time"]},
            )
            messages.success(request, "Working hours saved.")
    else:
        messages.error(request, "Please fill in the weekday, opening time and closing time.")
    return redirect("manage", slug=slug)


@owner_required
@require_POST
def hours_delete(request, pk):
    hours = get_object_or_404(WorkingHours, pk=pk, business__owner=request.user)
    slug = hours.business.slug
    hours.delete()
    messages.success(request, "Working hours removed.")
    return redirect("manage", slug=slug)


@owner_required
@require_POST
def booking_status(request, reference):
    """Owner confirms, completes or cancels a booking."""
    booking = get_object_or_404(Booking, reference=reference, business__owner=request.user)
    action = request.POST.get("action")
    allowed = {
        "confirm": (Booking.PENDING, Booking.CONFIRMED),
        "complete": (Booking.CONFIRMED, Booking.COMPLETED),
        "cancel": (None, Booking.CANCELLED),
    }
    if action in allowed and (allowed[action][0] in (None, booking.status)) and booking.status not in (Booking.CANCELLED, Booking.COMPLETED):
        booking.status = allowed[action][1]
        booking.save(update_fields=["status"])
        messages.success(request, f"Booking {booking.reference} is now {booking.get_status_display().lower()}.")
    else:
        messages.error(request, "That change is not allowed for this booking.")
    return redirect("manage", slug=booking.business.slug)
