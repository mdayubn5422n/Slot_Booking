from django import forms

from .models import Business, ContactMessage, Service, WorkingHours


class BusinessForm(forms.ModelForm):
    class Meta:
        model = Business
        fields = ["category", "name", "description", "address", "phone", "image", "is_active"]
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ["name", "duration_minutes", "price"]


class WorkingHoursForm(forms.ModelForm):
    class Meta:
        model = WorkingHours
        fields = ["weekday", "open_time", "close_time"]
        widgets = {
            "open_time": forms.TimeInput(attrs={"type": "time"}),
            "close_time": forms.TimeInput(attrs={"type": "time"}),
        }


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "message"]
        widgets = {"message": forms.Textarea(attrs={"rows": 5})}
