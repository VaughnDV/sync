from django.urls import path
from . import views

app_name = 'playlist_sync'

urlpatterns = [
    path('sync/', views.sync_playlist, name='sync'),
    path('review/<int:job_id>/', views.review_sync, name='review'),
] 