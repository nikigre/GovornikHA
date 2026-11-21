"""Config flow for the Govornik TTS integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .api import GovornikClient, GovornikConnectionError, GovornikError
from .const import CONF_VOICE, DOMAIN

_LOGGER = logging.getLogger(__name__)


def _voice_schema(voices: list[str], default: str | None) -> vol.Schema:
    """Build the voice selection schema."""
    if default not in voices:
        default = voices[0]
    return vol.Schema(
        {
            vol.Required(CONF_VOICE, default=default): SelectSelector(
                SelectSelectorConfig(
                    options=voices, mode=SelectSelectorMode.DROPDOWN
                )
            ),
        }
    )


async def _async_fetch_voices(flow: ConfigFlow | OptionsFlow) -> tuple[list[str], str | None]:
    """Fetch voices, returning (voices, error_key)."""
    client = GovornikClient(async_get_clientsession(flow.hass))
    try:
        voices = await client.async_get_voices()
    except GovornikConnectionError:
        return [], "cannot_connect"
    except GovornikError:
        _LOGGER.exception("Unexpected response from Govornik API")
        return [], "unknown"
    if not voices:
        return [], "no_voices"
    return voices, None


class GovornikConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Govornik TTS."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        if user_input and CONF_VOICE in user_input:
            return self.async_create_entry(title="Govornik", data=user_input)

        voices, error = await _async_fetch_voices(self)
        if error:
            # Show a retryable form instead of aborting; submitting it retries.
            return self.async_show_form(
                step_id="user", data_schema=vol.Schema({}), errors={"base": error}
            )

        return self.async_show_form(
            step_id="user", data_schema=_voice_schema(voices, None)
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> GovornikOptionsFlow:
        """Create the options flow."""
        return GovornikOptionsFlow()


class GovornikOptionsFlow(OptionsFlow):
    """Handle options for Govornik TTS."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        voices, error = await _async_fetch_voices(self)
        if error:
            return self.async_abort(reason=error)

        current = self.config_entry.options.get(
            CONF_VOICE, self.config_entry.data.get(CONF_VOICE)
        )
        return self.async_show_form(
            step_id="init", data_schema=_voice_schema(voices, current)
        )
