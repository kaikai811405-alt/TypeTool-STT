import sys
sys.stdout.reconfigure(encoding="utf-8")

import os
import time
import tempfile
import wave
from datetime import datetime
import numpy as np
import sounddevice as sd
import keyboard
import pyperclip
import torch
from silero_vad import load_silero_vad, get_speech_timestamps

from asr_engine import choose_engine, load_engine

# ===== 可調參數 =====
HOLD_KEYS = ["alt", "ctrl"]   # 觸發鍵（同時）。想換鍵改這裡，例如 ["ctrl", "space"]
EXIT_KEY = "esc"
MODE = "hold"          # "hold"=按住講話、放開結束；"toggle"=按一下開始、再按一下結束
SAMPLE_RATE = 16000
AUTO_PASTE = True      # True=自動貼到游標；False=只複製到剪貼簿
SAVE_HISTORY = True    # 每次口述存到 聽打紀錄.txt
VAD_PAD = 0.15         # 語音前後各保留秒數
VAD_THRESHOLD = 0.5    # VAD 靈敏度 0~1；若常漏掉小聲說話就調低（如 0.3）
RELEASE_DEBOUNCE = 3   # hold 模式：連續 N 次讀到放開才停止（濾抖動）
# ====================

_HERE = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(_HERE, "聽打紀錄.txt")

engine = load_engine(choose_engine(), short=True)
print("載入 VAD…")
_vad = load_silero_vad()

recording = []
is_recording = False


def start_recording():
    global recording, is_recording
    recording = []
    is_recording = True
    print("🎙️  錄音中…")


def vad_trim(audio):
    """去掉頭尾靜音；完全無語音回傳 None。"""
    ts = get_speech_timestamps(torch.from_numpy(audio), _vad,
                               sampling_rate=SAMPLE_RATE, threshold=VAD_THRESHOLD)
    if not ts:
        return None
    pad = int(VAD_PAD * SAMPLE_RATE)
    start = max(0, ts[0]["start"] - pad)
    end = min(len(audio), ts[-1]["end"] + pad)
    return audio[start:end]


def stop_and_transcribe():
    global is_recording
    is_recording = False
    if not recording:
        print("（沒錄到聲音）")
        return

    audio = np.concatenate(recording, axis=0).astype(np.float32).flatten()
    audio = vad_trim(audio)
    if audio is None or len(audio) < SAMPLE_RATE * 0.2:
        print("（未偵測到語音，略過）")
        return

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        with wave.open(f.name, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes((np.clip(audio, -1, 1) * 32767).astype(np.int16).tobytes())
        wav_path = f.name

    text = engine.text(wav_path)
    try:
        os.remove(wav_path)
    except OSError:
        pass

    if not text:
        print("（辨識為空，略過）")
        return

    print(f"📝 {text}")
    pyperclip.copy(text)
    if AUTO_PASTE:
        time.sleep(0.08)          # 等修飾鍵彈起，避免干擾 Ctrl+V
        keyboard.send("ctrl+v")
    if SAVE_HISTORY:
        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now():%Y-%m-%d %H:%M}] {text}\n")


def audio_callback(indata, frames, t, status):
    if is_recording:
        recording.append(indata.copy())


def keys_held():
    return all(keyboard.is_pressed(k) for k in HOLD_KEYS)


def wait_release():
    while keys_held():
        time.sleep(0.02)


combo = "+".join(HOLD_KEYS).upper()
if MODE == "toggle":
    print(f"就緒【toggle 模式】。按一下 {combo} 開始，再按一下結束並轉文字。按 {EXIT_KEY.upper()} 離開。")
else:
    print(f"就緒【按住模式】。按住 {combo} 講話，放開自動轉文字"
          + ("並貼到游標。" if AUTO_PASTE else "並複製到剪貼簿。")
          + f" 按 {EXIT_KEY.upper()} 離開。")

prev_held = False
released_count = 0

with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, callback=audio_callback):
    while True:
        if keyboard.is_pressed(EXIT_KEY):
            break
        held = keys_held()

        if MODE == "toggle":
            if held and not prev_held:          # 按下瞬間 = 一次切換
                if not is_recording:
                    start_recording()
                else:
                    stop_and_transcribe()
                wait_release()                  # 等放開，避免一次按住連續觸發
                prev_held = False
            else:
                prev_held = held
        else:  # hold
            if held and not is_recording:
                start_recording()
                released_count = 0
            elif is_recording:
                if held:
                    released_count = 0
                else:
                    released_count += 1
                    if released_count >= RELEASE_DEBOUNCE:
                        stop_and_transcribe()
                        wait_release()          # 等按鍵完全放開再待命
                        released_count = 0

        time.sleep(0.02)

print("已離開。")
