# Govornik TTS – Home Assistant Integration 🇸🇮

This is a custom [Text-to-Speech (TTS)](https://www.home-assistant.io/integrations/tts/) provider for [Home Assistant](https://www.home-assistant.io/), using the [Govornik API](https://govornik.eu/) to synthesize Slovenian speech.

Supports user-selectable voices and native Home Assistant UI configuration.

---

## ✅ Features

- 🗣️ Text-to-speech in **Slovenian** (`sl`)
- 🎙️ Voice selection (pulled live from Govornik `/voices` endpoint)
- ⚙️ Fully configurable via Home Assistant UI
- 📦 Clean integration with HA’s TTS engine
- 💬 MP3/WAV output via `media_player`, `automation`, etc.

---

## 📦 Installation

### Option 1: [HACS](https://hacs.xyz/)
Coming soon.

### Option 2: Manual

1. Clone this repository or download the ZIP
2. Copy the `govornik_tts` folder into your Home Assistant config directory:
3. Restart Home Assistant

---

## ⚙️ Configuration

After installing, add the integration via:

**Settings → Devices & Services → Add Integration → Search "Govornik TTS"**

You will be prompted to:

- 🎤 Select the desired **voice**

No YAML setup is required.

---

## 🔊 Usage Example

In your `scripts.yaml` or automation:

```yaml
service: tts.govornik_tts_say
data:
entity_id: media_player.living_room_speaker
message: "Pozdravljeni! To je test sinteze govora."
```

## 🌐 Supported Languages

| Code | Language   | Description           |
|------|------------|-----------------------|
| `sl` | Slovenian  | Slovenski jezik 🇸🇮     |

---

## 🛠️ Development Notes

- This integration communicates with the Govornik API at: `https://s1.govornik.eu`
- Voices are fetched from the `/voices` endpoint and cached locally
- Audio is generated via POST to `/` with parameters:
  - `voice`, `text`, `format`, `source`

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

## 🤝 Acknowledgments

- [Govornik TTS API](https://govornik.eu/)
- [Home Assistant](https://www.home-assistant.io/)
- Inspired by community TTS providers such as `google_translate` and `picotts`

---

## 💡 TODO

- [ ] HACS support
- [ ] Voice preview/test button in UI
- [ ] Caching of audio files for repeated phrases

---

## ✨ Screenshots

> Coming soon...

---

Made with ❤️ in 🇸🇮 for Home Assistant