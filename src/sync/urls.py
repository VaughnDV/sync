from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.dashboard.urls')),
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    path('playlist/', include('apps.playlist_sync.urls')),
    path('social-auth/', include('social_django.urls', namespace='social')),
] 