import io
import json
import os
import subprocess
import sys
import threading
import time
from dotenv import load_dotenv
import numpy as np
import sounddevice as sd
import soundfile as sf
from google import genai
from google.genai import types
from pynput import keyboard
import webview
import Quartz
from AppKit import NSScreen

load_dotenv()

# ----------------- CONFIGURATION -----------------
PUSH_TO_TALK_KEY = keyboard.Key.shift_r  # Right Shift key
SAMPLE_RATE = 16000
CHANNELS = 1
MODEL_NAME = "gemini-3.5-transcribe"

SOURCE_JSON = "siri_avi.json"
CLEAN_JSON = "siri_avi_clean.json"
# -------------------------------------------------

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ GEMINI_API_KEY not found in .env file.")
    sys.exit(1)

client = genai.Client(api_key=api_key)
kVK_ANSI_V = 9
FLAGS_CMD = Quartz.kCGEventFlagMaskCommand

# --- 1. STRIP THE EMBEDDED BLACK SOLID BACKGROUND ---
def clean_background():
    if not os.path.exists(SOURCE_JSON):
        print(f"⚠️ {SOURCE_JSON} not found in the current folder.")
        return

    with open(SOURCE_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Filter out Black Solid 1 and any pure black background layers
    if "layers" in data:
        data["layers"] = [
            l for l in data["layers"] 
            if not ("black solid" in l.get("nm", "").lower() or l.get("sc") == "#000000")
        ]

    with open(CLEAN_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f)
    print("✨ Black background stripped successfully for pure alpha transparency.")

clean_background()


# --- 2. HTML WITH CLEAN ALPHA VIEWPORT ---
HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    html, body {
      width: 100%;
      height: 100%;
      background: transparent !important;
      overflow: hidden;
      display: flex;
      align-items: center;
      justify-content: center;
      user-select: none;
      -webkit-user-select: none;
    }
    #lottie-box {
      width: 95px;
      height: 95px;
      opacity: 0;
      transform: scale(0.65);
      transition: opacity 0.16s ease-out, transform 0.22s cubic-bezier(0.175, 0.885, 0.32, 1.275);
      border-radius: 50%;
      filter: drop-shadow(0 4px 14px rgba(0,0,0,0.3));
      mix-blend-mode: screen;
    }
    #lottie-box.active {
      opacity: 1.0;
      transform: scale(1.0);
    }
    /* Processing indicator when Gemini is transcribing */
    #processing-indicator {
      display: none;
      width: 28px;
      height: 28px;
      border-radius: 50%;
      background: radial-gradient(circle, #38ef7d 0%, #11998e 100%);
      box-shadow: 0 0 16px #38ef7d;
      animation: pulse 0.6s infinite alternate ease-in-out;
    }
    @keyframes pulse {
      0% { transform: scale(0.75); opacity: 0.55; }
      100% { transform: scale(1.15); opacity: 1.0; }
    }
  </style>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/bodymovin/5.12.2/lottie.min.js"></script>
</head>
<body>
  <div id="lottie-box"></div>
  <div id="processing-indicator"></div>

  <script>
    let anim = null;
    const box = document.getElementById('lottie-box');
    const proc = document.getElementById('processing-indicator');

    fetch('siri_avi_clean.json')
      .then(r => r.json())
      .then(data => {
        anim = lottie.loadAnimation({
          container: box,
          renderer: 'svg',
          loop: true,
          autoplay: false,
          animationData: data
        });
      })
      .catch(e => console.error(e));

    window.hud = {
      startListening: function() {
        proc.style.display = 'none';
        box.style.display = 'block';
        box.className = 'active';
        if (anim) {
          anim.setSpeed(1.2);
          anim.play();
        }
      },
      setVolume: function(vol) {
        if (anim) {
          let speed = 0.85 + (vol * 2.4);
          anim.setSpeed(Math.min(3.0, speed));
        }
      },
      showProcessing: function() {
        if (anim) anim.stop();
        box.style.display = 'none';
        proc.style.display = 'block';
      },
      hideAll: function() {
        if (anim) anim.stop();
        box.className = '';
        proc.style.display = 'none';
      }
    };
  </script>
</body>
</html>
"""

with open("hud_siri.html", "w", encoding="utf-8") as f:
    f.write(HTML_TEMPLATE)


# --- 3. ZERO-LATENCY HARDWARE-LEVEL PASTE ---
def direct_mac_paste(text: str):
    p = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE, close_fds=True)
    p.communicate(input=text.encode("utf-8"))

    time.sleep(0.04)

    evt_down = Quartz.CGEventCreateKeyboardEvent(None, kVK_ANSI_V, True)
    Quartz.CGEventSetFlags(evt_down, FLAGS_CMD)
    Quartz.CGEventPost(Quartz.kCGAnnotatedSessionEventTap, evt_down)

    time.sleep(0.01)

    evt_up = Quartz.CGEventCreateKeyboardEvent(None, kVK_ANSI_V, False)
    Quartz.CGEventSetFlags(evt_up, FLAGS_CMD)
    Quartz.CGEventPost(Quartz.kCGAnnotatedSessionEventTap, evt_up)


def extract_transcription(response) -> str:
    try:
        if response.text:
            return response.text.strip()
    except Exception:
        pass

    try:
        if response.candidates:
            parts = response.candidates[0].content.parts
            texts = []
            for part in parts:
                if hasattr(part, "audio_transcription") and part.audio_transcription:
                    trans = part.audio_transcription
                    texts.append(getattr(trans, "text", str(trans)))
                elif hasattr(part, "text") and part.text:
                    texts.append(part.text)
            return " ".join(texts).strip()
    except Exception:
        pass

    return ""


# --- 4. ENGINE PIPELINE ---
class WisprFlowEngine:
    def __init__(self):
        self.window = None
        self.is_recording = False
        self.audio_frames = []
        self.stream = None
        self.lock = threading.Lock()

    def set_window(self, win):
        self.window = win

    def _audio_callback(self, indata, frames, time_info, status):
        if self.is_recording:
            self.audio_frames.append(indata.copy())
            rms = np.sqrt(np.mean(np.square(indata)))
            vol = min(1.0, float(rms * 16.0))
            if self.window:
                self.window.evaluate_js(f"window.hud.setVolume({vol:.2f});")

    def start_recording(self):
        with self.lock:
            if self.is_recording:
                return
            self.is_recording = True
            self.audio_frames = []

        if self.window:
            self.window.evaluate_js("window.hud.startListening();")

        print("\n🎙️ [Recording...] Speak now!", flush=True)

        self.stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="float32",
            callback=self._audio_callback,
        )
        self.stream.start()

    def stop_and_process(self):
        with self.lock:
            if not self.is_recording:
                return
            self.is_recording = False

        if self.window:
            self.window.evaluate_js("window.hud.showProcessing();")

        if self.stream:
            self.stream.stop()
            self.stream.close()

        if not self.audio_frames:
            if self.window:
                self.window.evaluate_js("window.hud.hideAll();")
            return

        print("\r⚡ [Transcribing...]", end="", flush=True)
        threading.Thread(target=self._process, args=(list(self.audio_frames),)).start()

    def _process(self, frames):
        t0 = time.time()
        try:
            audio_data = np.concatenate(frames, axis=0)

            if len(audio_data) < SAMPLE_RATE * 0.20:
                print("\r⚠️ Tap too brief, skipped.          ", flush=True)
                return

            wav_io = io.BytesIO()
            sf.write(wav_io, audio_data, SAMPLE_RATE, format="WAV", subtype="PCM_16")
            wav_bytes = wav_io.getvalue()

            t_api_start = time.time()
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=[
                    types.Part.from_bytes(data=wav_bytes, mime_type="audio/wav"),
                    "Transcribe accurately."
                ],
            )
            t_api = time.time() - t_api_start
            result_text = extract_transcription(response)
            total_time = time.time() - t0

            if not result_text:
                print(f"\r⚠️ Empty result ({total_time:.2f}s)       ", flush=True)
                return

            print(f"\r✅ Pasted ({total_time:.2f}s total | API: {t_api:.2f}s): \"{result_text}\"", flush=True)
            direct_mac_paste(result_text)

        except Exception as e:
            print(f"\r❌ Error: {e}                           ", flush=True)
        finally:
            if self.window:
                self.window.evaluate_js("window.hud.hideAll();")


engine = WisprFlowEngine()

def on_press(key):
    if key == PUSH_TO_TALK_KEY:
        engine.start_recording()

def on_release(key):
    if key == PUSH_TO_TALK_KEY:
        engine.stop_and_process()

def start_keyboard_listener():
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()


# --- 5. EXACT SCREEN BOTTOM-CENTER POSITIONING ---
def calculate_bottom_center(width=100, height=100, bottom_margin=80):
    screen = NSScreen.mainScreen().frame()
    screen_w = screen.size.width
    screen_h = screen.size.height

    # Calculate x for exact horizontal center
    x = int((screen_w - width) / 2)
    # Calculate y for bottom center (above Dock)
    y = int(screen_h - height - bottom_margin)
    return x, y


if __name__ == "__main__":
    threading.Thread(target=start_keyboard_listener, daemon=True).start()

    HUD_W, HUD_H = 100, 100
    pos_x, pos_y = calculate_bottom_center(width=HUD_W, height=HUD_H, bottom_margin=80)

    # Initialize transparent floating window positioned at the bottom-center
    hud_window = webview.create_window(
        title="WisprFlowHUD",
        url="hud_siri.html",
        width=HUD_W,
        height=HUD_H,
        x=pos_x,
        y=pos_y,
        frameless=True,
        on_top=True,
        transparent=True,
        easy_drag=False
    )
    engine.set_window(hud_window)

    print("=" * 60)
    print("🚀 Wispr Flow Bottom-Center Siri Orb Active")
    print("👉 HOLD [Right Shift (⇧)] to speak, RELEASE to paste.")
    print("👉 Orb is docked at bottom-center with zero background box.")
    print("=" * 60, flush=True)

    webview.start()