from django import forms
from .models import SyncJob

class SyncJobForm(forms.ModelForm):
    class Meta:
        model = SyncJob
        fields = ['youtube_playlist_url', 'spotify_playlist_name', 'spotify_playlist_id', 'reverse_order']
        widgets = {
            'youtube_playlist_url': forms.URLInput(attrs={
                'class': 'mt-1 block w-full rounded-md bg-gray-700 border-gray-600 text-gray-200 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 placeholder-gray-400',
                'placeholder': 'Enter YouTube playlist URL'
            }),
            'spotify_playlist_name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md bg-gray-700 border-gray-600 text-gray-200 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 placeholder-gray-400',
                'placeholder': 'Enter Spotify playlist name'
            }),
            'spotify_playlist_id': forms.HiddenInput(),
            'reverse_order': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 bg-gray-700 border-gray-600 text-indigo-600 focus:ring-indigo-500 focus:ring-offset-gray-800 rounded'
            }),
        }

class TrackMappingForm(forms.Form):
    spotify_track_id = forms.CharField(widget=forms.HiddenInput())
    spotify_track_name = forms.CharField(widget=forms.HiddenInput())
    spotify_artist_name = forms.CharField(widget=forms.HiddenInput())
    confidence_score = forms.FloatField(widget=forms.HiddenInput()) 