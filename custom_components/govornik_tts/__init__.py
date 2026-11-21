"""The Govornik TTS integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import GovornikClient, GovornikError

PLATFORMS: list[Platform] = [Platform.TTS]


@dataclass
class GovornikData:
    """Runtime data stored on the config entry."""

    client: GovornikClient
    voices: list[str]


type GovornikConfigEntry = ConfigEntry[GovornikData]


async def async_setup_entry(hass: HomeAssistant, entry: GovornikConfigEntry) -> bool:
    """Set up Govornik TTS from a config entry."""
    client = GovornikClient(async_get_clientsession(hass))
    try:
        voices = await client.async_get_voices()
    except GovornikError as err:
        raise ConfigEntryNotReady(f"Unable to reach Govornik API: {err}") from err

    entry.runtime_data = GovornikData(client=client, voices=voices)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: GovornikConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_update_listener(
    hass: HomeAssistant, entry: GovornikConfigEntry
) -> None:
    """Reload the entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
