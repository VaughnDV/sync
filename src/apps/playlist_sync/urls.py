from django.urls import path
from . import views

app_name = 'playlist_sync'

urlpatterns = [
    path('', views.sync_playlist, name='sync_playlist'),
    path('review/<int:job_id>/', views.review_sync, name='review'),
    path('status/<int:job_id>/', views.get_sync_status, name='status'),
    path('playlists/', views.get_playlists, name='get_playlists'),
] 