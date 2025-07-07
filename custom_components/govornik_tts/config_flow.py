"""Config flow for Govornik TTS integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import re
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

DOMAIN = "govornik_tts"

STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required("voice"): vol.In({}),  # Will be populated dynamically
})

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Govornik TTS."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self._voices = []
        self._errors = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is not None:
            return self.async_create_entry(
                title="Govornik TTS",
                data=user_input,
            )

        # Fetch voices first
        await self._fetch_voices()
        
        if not self._voices:
            return self.async_abort(reason="no_voices")

        # Create dynamic schema with available voices
        voice_options = {voice: voice for voice in self._voices}
        schema = vol.Schema({
            vol.Required("voice", default=self._voices[0]): vol.In(voice_options),
        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=self._errors,
        )

    async def _fetch_voices(self) -> None:
        """Fetch available voices from the Govornik API."""
        try:
            session = async_get_clientsession(self.hass)
            async with session.get("https://s1.govornik.eu/voices") as response:
                if response.status != 200:
                    _LOGGER.error("Failed to fetch voices: %s", await response.text())
                    self._voices = []
                    return
                    
                raw_voices = await response.text()
                self._voices = [
                    re.split(r'\s+', line)[0]
                    for line in raw_voices.splitlines()
                    if line.strip()
                ]
                _LOGGER.debug("Fetched voices: %s", self._voices)
                
        except aiohttp.ClientError as err:
            _LOGGER.error("Voice fetch error: %s", err)
            self._voices = []
        except Exception as err:
            _LOGGER.error("Unexpected error fetching voices: %s", err)
            self._voices = []

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> OptionsFlowHandler:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Govornik TTS."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        self._voices = []

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Fetch voices for options
        await self._fetch_voices()
        
        if not self._voices:
            return self.async_abort(reason="no_voices")

        # Get current voice from options (this is what we're trying to fix)
        current_voice = self.config_entry.options.get("voice")
        
        # If no voice in options yet, use the one from initial data
        if not current_voice:
            current_voice = self.config_entry.data.get("voice")
            
        # Debug logging
        _LOGGER.debug("Options voice: %s", self.config_entry.options.get("voice"))
        _LOGGER.debug("Data voice: %s", self.config_entry.data.get("voice"))
        _LOGGER.debug("Current voice selected: %s", current_voice)
        _LOGGER.debug("Available voices: %s", self._voices)
            
        # Ensure current voice is valid
        if current_voice not in self._voices:
            current_voice = self._voices[0] if self._voices else None
        
        # Create dynamic schema with available voices
        voice_options = {voice: voice for voice in self._voices}
        schema = vol.Schema({
            vol.Required("voice", default=current_voice): vol.In(voice_options),
        })

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
        )

    async def _fetch_voices(self) -> None:
        """Fetch available voices from the Govornik API."""
        try:
            session = async_get_clientsession(self.hass)
            async with session.get("https://s1.govornik.eu/voices") as response:
                if response.status != 200:
                    _LOGGER.error("Failed to fetch voices: %s", await response.text())
                    self._voices = []
                    return
                    
                raw_voices = await response.text()
                self._voices = [
                    re.split(r'\s+', line)[0]
                    for line in raw_voices.splitlines()
                    if line.strip()
                ]
                _LOGGER.debug("Fetched voices for options: %s", self._voices)
                
        except aiohttp.ClientError as err:
            _LOGGER.error("Voice fetch error in options: %s", err)
            self._voices = []
        except Exception as err:
            _LOGGER.error("Unexpected error fetching voices in options: %s", err)
            self._voices = []


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidVoice(HomeAssistantError):
    """Error to indicate there is invalid voice."""