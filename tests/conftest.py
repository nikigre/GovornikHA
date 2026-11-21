"""Shared fixtures for Govornik TTS tests."""

from __future__ import annotations

from collections.abc import Generator

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import (
    AiohttpClientMocker,
)

from custom_components.govornik_tts.const import (
    API_BASE_URL,
    API_VOICES_URL,
    CONF_VOICE,
    DOMAIN,
)

VOICES_RESPONSE = "ana    female  sl\nbor    male    sl\n\n"
VOICES = ["ana", "bor"]
AUDIO = b"ID3fake-mp3-bytes"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(
    enable_custom_integrations: None,
) -> Generator[None]:
    """Allow loading custom integrations in all tests."""
    yield


@pytest.fixture
def mock_voices(aioclient_mock: AiohttpClientMocker) -> AiohttpClientMocker:
    """Mock a successful voices response."""
    aioclient_mock.get(API_VOICES_URL, text=VOICES_RESPONSE)
    return aioclient_mock


@pytest.fixture
def mock_synthesis(mock_voices: AiohttpClientMocker) -> AiohttpClientMocker:
    """Mock a successful synthesis response (plus voices)."""
    mock_voices.post(
        API_BASE_URL, content=AUDIO, headers={"Content-Type": "audio/mpeg"}
    )
    return mock_voices


@pytest.fixture
def config_entry() -> MockConfigEntry:
    """Return a Govornik config entry."""
    return MockConfigEntry(
        domain=DOMAIN, title="Govornik", data={CONF_VOICE: "ana"}
    )
