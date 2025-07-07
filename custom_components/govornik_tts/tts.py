"""Platform for Govornik TTS speech service."""
from homeassistant.components.tts import Provider, TtsAudioType
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
import aiohttp
import logging
import re

_LOGGER = logging.getLogger(__name__)

DOMAIN = "govornik_tts"

async def async_get_engine(
    hass: HomeAssistant,
    config: ConfigType,
    discovery_info: DiscoveryInfoType | None = None,
) -> Provider:
    """Set up Govornik TTS."""
    return GovornikProvider(hass, config)

class GovornikProvider(Provider):
    """Govornik TTS provider."""
    
    def __init__(self, hass, config):
        self.hass = hass
        self.name = "Govornik"
        self._session = async_get_clientsession(hass)
        self._voices = []
        self._voice_cache = None
        self._config = config

    def _get_configured_voice(self):
        """Get the currently configured voice from config entry."""
        config_entries = self.hass.config_entries.async_entries("govornik_tts")
        if config_entries:
            entry = config_entries[0]
            # Only use options (updated settings)
            return entry.options.get("voice")
        return None

    @property
    def default_language(self):
        return "sl"

    @property
    def supported_languages(self):
        return ["sl"]

    @property
    def supported_options(self):
        """Return list of supported options."""
        return ["voice", "format"]

    def _get_configured_voice(self):
        """Get the currently configured voice from config entry."""
        config_entries = self.hass.config_entries.async_entries("govornik_tts")
        if config_entries:
            entry = config_entries[0]
            # Check options first (updated settings), then data (initial settings)
            return entry.options.get("voice") or entry.data.get("voice")
        return None

    async def async_init(self):
        """Initialize voice list."""
        if not self._voice_cache:
            await self._fetch_voices()

    async def _fetch_voices(self):
        """Get available voices from API."""
        try:
            async with self._session.get("https://s1.govornik.eu/voices") as response:
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
                self._voice_cache = self._voices
                _LOGGER.debug("Available voices: %s", self._voices)
                
        except aiohttp.ClientError as err:
            _LOGGER.error("Voice fetch error: %s", err)
            self._voices = []

    async def async_get_tts_audio(self, message: str, language: str, options: dict) -> TtsAudioType:
        """Generate TTS audio using Govornik API."""
        await self.async_init()
        
        # Format validation
        fmt = options.get("format", "mp3").lower()
        if fmt not in ["mp3", "wav"]:
            _LOGGER.warning("Invalid format '%s'. Defaulting to mp3", fmt)
            fmt = "mp3"
        
        # Voice selection priority: options only
        voice = options.get("voice") or self._get_configured_voice()
        
        if not voice:
            _LOGGER.error("No voice configured.")
            return None
        
        if not voice:
            _LOGGER.error("No voices available.")
            return None
            
        if self._voices and voice not in self._voices:
            _LOGGER.error("Invalid voice selected: %s. Available voices: %s", voice, self._voices)
            return None

        params = {
            "voice": voice,
            "source": "HomeAssistant",
            "format": fmt,
            "text": message
        }
        
        try:
            async with self._session.post("https://s1.govornik.eu", data=params) as response:
                if response.status != 200:
                    _LOGGER.error("API error: %s", await response.text())
                    return None
                    
                content_type = response.headers.get("Content-Type", "").lower()
                audio_data = await response.read()
                
                # Determine correct format from response
                if "wav" in content_type:
                    detected_format = "wav"
                elif "mp3" in content_type or "mpeg" in content_type:
                    detected_format = "mp3"
                else:
                    _LOGGER.warning("Unknown content type '%s', assuming mp3", content_type)
                    detected_format = "mp3"
                    
                return (detected_format, audio_data)
                
        except aiohttp.ClientError as err:
            _LOGGER.error("Connection error: %s", err)
            return None

    async def async_get_supported_voices(self, language: str):
        """Return list of supported voices for given language."""
        await self.async_init()
        return self._voices if language == "sl" else []