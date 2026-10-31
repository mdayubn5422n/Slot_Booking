from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect, render

from .forms import SignupForm
from .models import is_owner


def signup(request):
    """Create a new account and log the person in."""
    if request.user.is_authenticated:
        return redirect("home")
    form = SignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Your account is ready. Welcome to SlotBook!")
        return redirect("owner_dashboard" if is_owner(user) else "home")
    return render(request, "accounts/signup.html", {"form": form})
