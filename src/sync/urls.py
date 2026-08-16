from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from sync.health import live, ready


def metrics(_request):
    return HttpResponse(generate_latest(), content_type=CONTENT_TYPE_LATEST)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.dashboard.urls")),
    path("accounts/", include("apps.accounts.urls", namespace="accounts")),
    path("playlist/", include("apps.playlist_sync.urls")),
    path("social-auth/", include("social_django.urls", namespace="social")),
    path("health/live/", live, name="health-live"),
    path("health/ready/", ready, name="health-ready"),
    path("health/", live, name="health"),
    path("metrics/", metrics, name="metrics"),
]
