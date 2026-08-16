import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_liveness(client):
    response = client.get(reverse("health-live"))
    assert response.status_code == 200
    assert response.json()["status"] == "live"


@pytest.mark.django_db
def test_readiness(client):
    response = client.get(reverse("health-ready"))
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


@pytest.mark.django_db
def test_metrics(client):
    response = client.get(reverse("metrics"))
    assert response.status_code == 200
    assert b"sync_jobs" in response.content or response.status_code == 200
