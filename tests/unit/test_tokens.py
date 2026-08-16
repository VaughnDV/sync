import pytest
from django.db import connection

from apps.accounts.models import User
from django.contrib.admin.sites import site


@pytest.mark.django_db
def test_tokens_encrypted_at_rest(user):
    with connection.cursor() as cursor:
        cursor.execute("SELECT spotify_access_token FROM accounts_user WHERE id = %s", [user.pk])
        raw = cursor.fetchone()[0]
    assert raw
    assert raw != "access-token"
    assert "access-token" not in raw
    loaded = User.objects.get(pk=user.pk)
    assert loaded.spotify_access_token == "access-token"


@pytest.mark.django_db
def test_repr_and_admin_omit_tokens(user):
    text = repr(user)
    assert "access-token" not in text
    admin = site._registry[User]
    flattened = []
    for _name, opts in admin.fieldsets:
        flattened.extend(opts["fields"])
    assert "spotify_access_token" not in flattened
    assert "spotify_refresh_token" not in flattened
    assert "spotify_connected" in flattened
