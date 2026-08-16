from __future__ import annotations

import os

from tests.settings import *  # noqa: F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "sync"),
        "USER": os.getenv("POSTGRES_USER", "sync"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "sync"),
        "HOST": os.getenv("POSTGRES_HOST", "127.0.0.1"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
    }
}
