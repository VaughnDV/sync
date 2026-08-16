from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
from django.views.generic import CreateView
from django.urls import reverse_lazy

from providers.factory import get_spotify_client

from .forms import UserLoginForm, UserRegistrationForm


class RegisterView(CreateView):
    form_class = UserRegistrationForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("accounts:login")


def login_view(request):
    if request.method == "POST":
        form = UserLoginForm(request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            return redirect("dashboard:dashboard")
    else:
        form = UserLoginForm()
    return render(request, "accounts/login.html", {"form": form})


@require_POST
@login_required
def logout_view(request):
    logout(request)
    return redirect("accounts:login")


@login_required
def disconnect_spotify(request):
    if request.method == "POST":
        client = get_spotify_client(request.user)
        client.disconnect()
        request.user.clear_spotify_credentials()
        request.user.save(
            update_fields=[
                "spotify_access_token",
                "spotify_refresh_token",
                "spotify_token_expires_at",
                "spotify_connected",
            ]
        )
        return redirect("dashboard:dashboard")
    return render(request, "accounts/disconnect.html")
