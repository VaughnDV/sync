from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db import models


def _fernet() -> Fernet:
    key = settings.TOKEN_ENCRYPTION_KEY
    if isinstance(key, str):
        key = key.encode()
    return Fernet(key)


class EncryptedTextField(models.TextField):
    """Fernet-encrypted text that never returns ciphertext to application code."""

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        return name, "apps.accounts.crypto.EncryptedTextField", args, kwargs

    def from_db_value(self, value, expression, connection):
        if not value:
            return ""
        try:
            return _fernet().decrypt(value.encode()).decode()
        except (InvalidToken, ValueError, TypeError):
            return ""

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if not value:
            return ""
        return _fernet().encrypt(str(value).encode()).decode()
