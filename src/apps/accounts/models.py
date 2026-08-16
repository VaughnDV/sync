from django.contrib.auth.models import AbstractUser
from django.db import models

from .crypto import EncryptedTextField


class User(AbstractUser):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    spotify_access_token = EncryptedTextField(blank=True, default="")
    spotify_refresh_token = EncryptedTextField(blank=True, default="")
    spotify_token_expires_at = models.DateTimeField(null=True, blank=True)
    spotify_connected = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self) -> str:
        return self.email

    def __repr__(self) -> str:
        return f"<User id={self.pk} email={self.email!r} connected={self.spotify_connected}>"

    def clear_spotify_credentials(self) -> None:
        self.spotify_access_token = ""
        self.spotify_refresh_token = ""
        self.spotify_token_expires_at = None
        self.spotify_connected = False
