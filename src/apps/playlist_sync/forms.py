from django import forms
from .models import SyncJob

class SyncJobForm(forms.ModelForm):
    class Meta:
        model = SyncJob
        fields = ['youtube_playlist_url', 'spotify_playlist_name', 'reverse_order']
        widgets = {
            'youtube_playlist_url': forms.URLInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'Enter YouTube playlist URL'
            }),
            'spotify_playlist_name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'Enter Spotify playlist name'
            }),
            'reverse_order': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded'
            }),
        }

class TrackMappingForm(forms.Form):
    spotify_track_id = forms.CharField(widget=forms.HiddenInput())
    spotify_track_name = forms.CharField(widget=forms.HiddenInput())
    spotify_artist_name = forms.CharField(widget=forms.HiddenInput())
    confidence_score = forms.FloatField(widget=forms.HiddenInput()) 