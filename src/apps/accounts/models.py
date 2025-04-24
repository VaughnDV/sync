from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    spotify_access_token = models.CharField(max_length=1000, blank=True, null=True)
    spotify_refresh_token = models.CharField(max_length=1000, blank=True, null=True)
    spotify_token_expires_at = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email 