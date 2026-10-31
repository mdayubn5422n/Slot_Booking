from django.urls import path

from . import views

urlpatterns = [
    # Public pages
    path("", views.home, name="home"),
    path("businesses/", views.business_list, name="business_list"),
    path("business/<slug:slug>/", views.business_detail, name="business_detail"),
    path("contact/", views.contact, name="contact"),
    # Customer pages
    path("business/<slug:slug>/book/", views.book, name="book"),
    path("booking/<str:reference>/", views.booking_detail, name="booking_detail"),
    path("my-bookings/", views.my_bookings, name="my_bookings"),
    path("my-bookings/<str:reference>/cancel/", views.cancel_booking, name="cancel_booking"),
    # Business Owner pages
    path("owner/", views.owner_dashboard, name="owner_dashboard"),
    path("owner/business/new/", views.business_form, name="business_create"),
    path("owner/business/<slug:slug>/edit/", views.business_form, name="business_edit"),
    path("owner/business/<slug:slug>/", views.manage, name="manage"),
    path("owner/business/<slug:slug>/service/add/", views.service_add, name="service_add"),
    path("owner/service/<int:pk>/delete/", views.service_delete, name="service_delete"),
    path("owner/business/<slug:slug>/hours/add/", views.hours_add, name="hours_add"),
    path("owner/hours/<int:pk>/delete/", views.hours_delete, name="hours_delete"),
    path("owner/booking/<str:reference>/status/", views.booking_status, name="booking_status"),
]
