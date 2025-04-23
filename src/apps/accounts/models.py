from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    spotify_access_token = models.CharField(max_length=255, blank=True, null=True)
    spotify_refresh_token = models.CharField(max_length=255, blank=True, null=True)
    spotify_token_expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.email 