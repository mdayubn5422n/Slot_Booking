from django.contrib import admin
from django.utils.html import format_html

from .models import FAQ, Booking, Business, Category, ContactMessage, Service, SiteImage, WorkingHours


def thumb(obj):
    """Small image preview in the admin list."""
    if obj.image:
        return format_html('<img src="{}" style="height:40px;border-radius:4px">', obj.image.url)
    return "-"


thumb.short_description = "Image"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", thumb)
    prepopulated_fields = {"slug": ("name",)}


class ServiceInline(admin.TabularInline):
    model = Service
    extra = 0


class HoursInline(admin.TabularInline):
    model = WorkingHours
    extra = 0


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "owner", "is_active", thumb)
    list_filter = ("category", "is_active")
    search_fields = ("name", "owner__username")
    inlines = [ServiceInline, HoursInline]


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("reference", "business", "customer", "date", "start_time", "status", "utm_source")
    list_filter = ("status", "date", "business")
    search_fields = ("reference", "customer__username", "business__name")


@admin.register(SiteImage)
class SiteImageAdmin(admin.ModelAdmin):
    list_display = ("key", "alt_text", thumb)


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question", "order", "is_published")
    list_editable = ("order", "is_published")


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "created_at", "utm_source")
    readonly_fields = ("created_at",)
