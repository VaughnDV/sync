from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.dashboard.urls")),
    path("accounts/", include("apps.accounts.urls", namespace="accounts")),
    path("playlist/", include("apps.playlist_sync.urls")),
    path("social-auth/", include("social_django.urls", namespace="social")),
    path("health/", TemplateView.as_view(template_name="health.html"), name="health"),
]
