"""Async client for the Govornik TTS API."""

from __future__ import annotations

import asyncio
import logging

import aiohttp

from .const import API_BASE_URL, API_SOURCE, API_TIMEOUT, API_VOICES_URL

_LOGGER = logging.getLogger(__name__)


class GovornikError(Exception):
    """Base error for the Govornik API."""


class GovornikConnectionError(GovornikError):
    """Error communicating with the Govornik API."""


class GovornikApiError(GovornikError):
    """The Govornik API returned an error response."""


class GovornikClient:
    """Minimal async client for the Govornik API."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        """Initialize the client with a shared aiohttp session."""
        self._session = session
        self._timeout = aiohttp.ClientTimeout(total=API_TIMEOUT)

    async def async_get_voices(self) -> list[str]:
        """Return the list of available voice identifiers."""
        try:
            async with self._session.get(
                API_VOICES_URL, timeout=self._timeout
            ) as response:
                text = await response.text()
                if response.status != 200:
                    raise GovornikApiError(
                        f"Fetching voices failed ({response.status}): {text}"
                    )
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise GovornikConnectionError(f"Error fetching voices: {err}") from err

        voices = [line.split()[0] for line in text.splitlines() if line.strip()]
        _LOGGER.debug("Fetched voices: %s", voices)
        return voices

    async def async_synthesize(
        self, text: str, voice: str, audio_format: str
    ) -> tuple[str, bytes]:
        """Synthesize speech and return (extension, audio bytes)."""
        payload = {
            "voice": voice,
            "source": API_SOURCE,
            "format": audio_format,
            "text": text,
        }
        try:
            async with self._session.post(
                API_BASE_URL, data=payload, timeout=self._timeout
            ) as response:
                if response.status != 200:
                    raise GovornikApiError(
                        f"Synthesis failed ({response.status}): "
                        f"{await response.text()}"
                    )
                content_type = response.content_type.lower()
                audio = await response.read()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise GovornikConnectionError(f"Error synthesizing speech: {err}") from err

        if "wav" in content_type:
            extension = "wav"
        elif "mpeg" in content_type or "mp3" in content_type:
            extension = "mp3"
        else:
            _LOGGER.debug(
                "Unexpected content type %s, assuming %s", content_type, audio_format
            )
            extension = audio_format
        return extension, audio
