from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from django.test import override_settings

from providers import factory as provider_factory
from providers.fakes import FakeSongClassifier, FakeSpotifyClient, FakeYouTubeClient


@pytest.fixture(autouse=True)
def reset():
    provider_factory.reset_fakes()
    yield
    provider_factory.reset_fakes()


@pytest.fixture()
def fake_user():
    return MagicMock(name="fake_user")


@override_settings(SYNC_PROVIDER_MODE="fake")
def test_get_youtube_client_fake():
    client = provider_factory.get_youtube_client()
    assert isinstance(client, FakeYouTubeClient)


@override_settings(SYNC_PROVIDER_MODE="fake")
def test_get_spotify_client_fake(fake_user):
    client = provider_factory.get_spotify_client(fake_user)
    assert isinstance(client, FakeSpotifyClient)


@override_settings(SYNC_PROVIDER_MODE="fake")
def test_get_spotify_client_reuses_instance(fake_user):
    c1 = provider_factory.get_spotify_client(fake_user)
    c2 = provider_factory.get_spotify_client(fake_user)
    assert c1 is c2


@override_settings(SYNC_PROVIDER_MODE="fake")
def test_get_classifier_fake():
    classifier = provider_factory.get_classifier()
    assert isinstance(classifier, FakeSongClassifier)


@override_settings(SYNC_PROVIDER_MODE="fake")
def test_get_classifier_reuses_instance():
    c1 = provider_factory.get_classifier()
    c2 = provider_factory.get_classifier()
    assert c1 is c2


@override_settings(SYNC_PROVIDER_MODE="fake")
def test_reset_fakes_clears_singletons(fake_user):
    provider_factory.get_spotify_client(fake_user)
    provider_factory.get_classifier()
    provider_factory.reset_fakes()
    assert provider_factory._fake_spotify is None
    assert provider_factory._fake_classifier is None
