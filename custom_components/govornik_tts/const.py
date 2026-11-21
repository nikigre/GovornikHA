"""Constants for the Govornik TTS integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "govornik_tts"

API_BASE_URL: Final = "https://s1.govornik.eu"
API_VOICES_URL: Final = f"{API_BASE_URL}/voices"
API_SOURCE: Final = "HomeAssistant"
API_TIMEOUT: Final = 30

CONF_VOICE: Final = "voice"
CONF_FORMAT: Final = "format"

DEFAULT_LANGUAGE: Final = "sl"
SUPPORTED_LANGUAGES: Final = [DEFAULT_LANGUAGE]

DEFAULT_FORMAT: Final = "mp3"
SUPPORTED_FORMATS: Final = ["mp3", "wav"]
