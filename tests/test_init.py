"""Tests for Govornik TTS setup and unload."""

from __future__ import annotations

import asyncio

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import (
    AiohttpClientMocker,
)

from custom_components.govornik_tts.const import API_VOICES_URL

from .conftest import VOICES


async def test_setup_and_unload(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_voices: AiohttpClientMocker,
) -> None:
    """Test the entry sets up, exposes the entity and unloads."""
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED
    assert config_entry.runtime_data.voices == VOICES
    assert hass.states.get("tts.govornik") is not None

    assert await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.NOT_LOADED


async def test_setup_retry_when_api_unreachable(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test setup is retried when voices cannot be fetched."""
    aioclient_mock.get(API_VOICES_URL, exc=asyncio.TimeoutError())
    config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.SETUP_RETRY
