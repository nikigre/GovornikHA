"""Text-to-speech entity for Govornik."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.tts import (
    ATTR_VOICE,
    TextToSpeechEntity,
    TtsAudioType,
    Voice,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import GovornikConfigEntry
from .api import GovornikError
from .const import (
    CONF_FORMAT,
    CONF_VOICE,
    DEFAULT_FORMAT,
    DEFAULT_LANGUAGE,
    DOMAIN,
    SUPPORTED_FORMATS,
    SUPPORTED_LANGUAGES,
)

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GovornikConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Govornik TTS entity from a config entry."""
    async_add_entities([GovornikTTSEntity(entry)])


class GovornikTTSEntity(TextToSpeechEntity):
    """Govornik text-to-speech entity."""

    # The TTS manager requires a non-empty engine name, so this entity is not
    # named after its device (same pattern as the core google_translate TTS).
    _attr_name = "Govornik"
    _attr_default_language = DEFAULT_LANGUAGE
    _attr_supported_languages = SUPPORTED_LANGUAGES
    _attr_supported_options = [ATTR_VOICE, CONF_FORMAT]

    def __init__(self, entry: GovornikConfigEntry) -> None:
        """Initialize the entity."""
        self._entry = entry
        self._client = entry.runtime_data.client
        self._voices = entry.runtime_data.voices
        self._attr_unique_id = entry.entry_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Govornik",
            manufacturer="Govornik",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url="https://govornik.eu",
        )

    @property
    def default_options(self) -> dict[str, Any]:
        """Return the default options (used for caching)."""
        return {
            ATTR_VOICE: self._configured_voice,
            CONF_FORMAT: DEFAULT_FORMAT,
        }

    @property
    def _configured_voice(self) -> str | None:
        """Return the voice configured via options, falling back to setup data."""
        return self._entry.options.get(CONF_VOICE) or self._entry.data.get(CONF_VOICE)

    @callback
    def async_get_supported_voices(self, language: str) -> list[Voice] | None:
        """Return the voices supported for a language."""
        if language not in SUPPORTED_LANGUAGES:
            return None
        return [Voice(voice_id=voice, name=voice) for voice in self._voices]

    async def async_get_tts_audio(
        self, message: str, language: str, options: dict[str, Any]
    ) -> TtsAudioType:
        """Generate speech audio for a message."""
        voice = options.get(ATTR_VOICE) or self._configured_voice
        if not voice:
            raise HomeAssistantError("No Govornik voice configured")
        if self._voices and voice not in self._voices:
            raise HomeAssistantError(
                f"Unknown Govornik voice '{voice}'. "
                f"Available voices: {', '.join(self._voices)}"
            )

        audio_format = str(options.get(CONF_FORMAT, DEFAULT_FORMAT)).lower()
        if audio_format not in SUPPORTED_FORMATS:
            raise HomeAssistantError(
                f"Unsupported format '{audio_format}'. "
                f"Use one of: {', '.join(SUPPORTED_FORMATS)}"
            )

        try:
            return await self._client.async_synthesize(message, voice, audio_format)
        except GovornikError as err:
            _LOGGER.error("Govornik speech synthesis failed: %s", err)
            raise HomeAssistantError(f"Govornik speech synthesis failed: {err}") from err
