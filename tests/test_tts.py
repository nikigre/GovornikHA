"""Tests for the Govornik TTS entity."""

from __future__ import annotations

import asyncio
from typing import Any
from urllib.parse import parse_qs

import pytest
from homeassistant.components import tts
from homeassistant.components.tts import ATTR_VOICE
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_component import DATA_INSTANCES
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import (
    AiohttpClientMocker,
)

from custom_components.govornik_tts.const import API_BASE_URL, CONF_VOICE
from custom_components.govornik_tts.tts import GovornikTTSEntity

from .conftest import AUDIO, VOICES


@pytest.fixture
async def entity(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_synthesis: AiohttpClientMocker,
) -> GovornikTTSEntity:
    """Set up the integration and return the TTS entity."""
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    tts_entity = hass.data[DATA_INSTANCES]["tts"].get_entity("tts.govornik")
    assert isinstance(tts_entity, GovornikTTSEntity)
    return tts_entity


def _last_payload(aioclient_mock: AiohttpClientMocker) -> dict[str, Any]:
    """Return the form payload of the last synthesis request."""
    method, url, data, _ = aioclient_mock.mock_calls[-1]
    assert method == "POST"
    assert str(url) == API_BASE_URL
    if isinstance(data, bytes):
        data = data.decode()
    if isinstance(data, str):
        return {key: values[0] for key, values in parse_qs(data).items()}
    return dict(data)


async def test_full_tts_pipeline(
    hass: HomeAssistant,
    entity: GovornikTTSEntity,
    mock_synthesis: AiohttpClientMocker,
) -> None:
    """Test audio generation through the TTS manager (as tts.speak does)."""
    assert entity.name == "Govornik"
    media_id = tts.generate_media_source_id(
        hass,
        "Živjo",
        engine="tts.govornik",
        language="sl",
        options={ATTR_VOICE: "bor"},
        cache=False,
    )
    assert await tts.async_get_media_source_audio(hass, media_id) == ("mp3", AUDIO)
    assert _last_payload(mock_synthesis)["voice"] == "bor"


async def test_entity_properties(entity: GovornikTTSEntity) -> None:
    """Test languages, options and voices."""
    assert entity.default_language == "sl"
    assert entity.supported_languages == ["sl"]
    assert set(entity.supported_options) == {ATTR_VOICE, "format"}
    assert entity.default_options == {ATTR_VOICE: "ana", "format": "mp3"}
    voices = entity.async_get_supported_voices("sl")
    assert [v.voice_id for v in voices] == VOICES
    assert entity.async_get_supported_voices("en") is None


async def test_get_audio_uses_configured_voice(
    entity: GovornikTTSEntity, mock_synthesis: AiohttpClientMocker
) -> None:
    """Test synthesis with the configured voice."""
    assert await entity.async_get_tts_audio("Živjo", "sl", {}) == ("mp3", AUDIO)
    payload = _last_payload(mock_synthesis)
    assert payload == {
        "voice": "ana",
        "source": "HomeAssistant",
        "format": "mp3",
        "text": "Živjo",
    }


async def test_get_audio_voice_override(
    entity: GovornikTTSEntity, mock_synthesis: AiohttpClientMocker
) -> None:
    """Test a per-call voice override."""
    await entity.async_get_tts_audio("Živjo", "sl", {ATTR_VOICE: "bor"})
    assert _last_payload(mock_synthesis)["voice"] == "bor"


async def test_options_voice_takes_precedence(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_synthesis: AiohttpClientMocker,
) -> None:
    """Test the options voice overrides the setup voice."""
    config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(config_entry, options={CONF_VOICE: "bor"})
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    tts_entity = hass.data[DATA_INSTANCES]["tts"].get_entity("tts.govornik")

    await tts_entity.async_get_tts_audio("Živjo", "sl", {})
    assert _last_payload(mock_synthesis)["voice"] == "bor"


@pytest.mark.parametrize(
    "options",
    [{ATTR_VOICE: "unknown"}, {"format": "ogg"}],
)
async def test_invalid_options_raise(
    entity: GovornikTTSEntity, options: dict[str, Any]
) -> None:
    """Test invalid voice or format raise an error."""
    with pytest.raises(HomeAssistantError):
        await entity.async_get_tts_audio("Živjo", "sl", options)


async def test_wav_content_type(
    entity: GovornikTTSEntity, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test the returned extension follows the response content type."""
    aioclient_mock.clear_requests()
    aioclient_mock.post(
        API_BASE_URL, content=b"RIFF", headers={"Content-Type": "audio/wav"}
    )
    assert await entity.async_get_tts_audio("Živjo", "sl", {"format": "wav"}) == (
        "wav",
        b"RIFF",
    )


@pytest.mark.parametrize(
    "mock_kwargs",
    [{"status": 500, "text": "error"}, {"exc": asyncio.TimeoutError()}],
)
async def test_api_failure_raises(
    entity: GovornikTTSEntity,
    aioclient_mock: AiohttpClientMocker,
    mock_kwargs: dict[str, Any],
) -> None:
    """Test API failures surface as HomeAssistantError."""
    aioclient_mock.clear_requests()
    aioclient_mock.post(API_BASE_URL, **mock_kwargs)
    with pytest.raises(HomeAssistantError):
        await entity.async_get_tts_audio("Živjo", "sl", {})
