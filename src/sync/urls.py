from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.dashboard.urls')),
    path('accounts/', include('apps.accounts.urls')),
    path('playlist/', include('apps.playlist_sync.urls')),
    path('social-auth/', include('social_django.urls', namespace='social')),
] 