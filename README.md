# WisprFree

> Free, open-source macOS voice-to-paste — because $15/month for dictation felt wrong when the free API tier exists.

Hold **Right Shift**, speak, release. Your words are transcribed by Gemini and instantly pasted into whatever app is active.

**[Interactive README →](https://claude.ai/artifact/NAsxsvfFqg64aU5yD2c7xp)**

---

## How it works

1. **Hold Right Shift** — a Siri-style floating orb appears at the bottom of your screen
2. **Speak** — audio streams into a 16 kHz buffer; the orb reacts to your volume
3. **Release** — the WAV chunk is sent to `gemini-3.5-transcribe`
4. **Text appears** — result is pasted via a hardware-level Quartz Cmd+V event, works in any app

## Requirements

- macOS (uses `Quartz`, `AppKit`, `pywebview`)
- Python 3.11+
- [Google AI Studio](https://aistudio.google.com) API key (free tier works)
- Accessibility permissions for keyboard listener + paste

## macOS permissions

This app needs three system permissions. macOS will prompt for each the first time — you can also grant them upfront.

### 1. Microphone
**System Settings → Privacy & Security → Microphone** — enable for Terminal (or your Python app).

The script won't record anything if this is missing; `sounddevice` will open a silent stream.

### 2. Accessibility
**System Settings → Privacy & Security → Accessibility** — enable for Terminal.

Required for the keyboard listener (`pynput`) to detect Right Shift globally, and for Quartz to fire the hardware Cmd+V paste. Without it, the hotkey is silently ignored.

> **Why does it need Accessibility?** macOS restricts apps from monitoring keypresses or synthesising keyboard events unless they're explicitly trusted. This is the same permission Wispr Flow, Alfred, and Raycast require.

### 3. Input Monitoring (macOS 14+)
**System Settings → Privacy & Security → Input Monitoring** — enable for Terminal.

On Sonoma and later, global key listeners also need Input Monitoring on top of Accessibility. If the orb never appears when you press Right Shift, this is usually why.

---

**One-time trust prompt:** The first run may show a dialog — *"Terminal.app" wants to monitor input from your keyboard.* Click **OK**. If you accidentally clicked Don't Allow, go to Input Monitoring in System Settings, remove Terminal, re-add it, and relaunch.

---

## Setup

```bash
git clone https://github.com/avinashnahar/wisprfree
cd wisprfree
pip install -r requirements.txt
echo "GEMINI_API_KEY=your_key_here" > .env
python wispr_avi_hud.py
```

## Files

| File | Purpose |
|------|---------|
| `wispr_avi_hud.py` | Main script |
| `siri_avi.json` | Lottie animation source (alpha-stripped at runtime) |
| `requirements.txt` | Python dependencies |

`siri_avi_clean.json` and `hud_siri.html` are generated at runtime and gitignored.

## vs Wispr Flow

| | Wispr Flow | WisprFree |
|---|---|---|
| Push-to-talk anywhere | ✓ | ✓ |
| Floating HUD | ✓ | ✓ |
| Auto-paste | ✓ | ✓ |
| Price | $15/mo | $0 |
| Open source | ✗ | ✓ |
| AI rewrites / commands | ✓ | ✗ |

## License

MIT
