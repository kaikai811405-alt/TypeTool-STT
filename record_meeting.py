import sys
import os
sys.stdout.reconfigure(encoding="utf-8")

import time
import wave
import threading
import subprocess
import numpy as np
import soundcard as sc

from asr_engine import choose_engine, load_engine

# ===== 可調參數 =====
SR = 16000          # 取樣率
CHUNK = 1024        # 每次讀取的音框
# ====================

# 錄音輸出夾：可用環境變數 TYPETOOL_REC_DIR 指定；預設放本程式資料夾下的「會議錄音」
OUT_DIR = os.environ.get("TYPETOOL_REC_DIR") or os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "會議錄音")
os.makedirs(OUT_DIR, exist_ok=True)

stamp = time.strftime("%Y%m%d_%H%M")
base = os.path.join(OUT_DIR, f"會議錄音_{stamp}")
mic_wav = base + "_mic.tmp.wav"
sys_wav = base + "_sys.tmp.wav"
final_wav = base + ".wav"

stop_event = threading.Event()


def record_source(source, wav_path, label):
    """從單一音源持續錄音寫入 wav，直到 stop_event 被設定。"""
    try:
        with wave.open(wav_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SR)
            with source.recorder(samplerate=SR, channels=1) as r:
                while not stop_event.is_set():
                    data = r.record(numframes=CHUNK)
                    pcm = (np.clip(data[:, 0], -1.0, 1.0) * 32767).astype(np.int16)
                    wf.writeframes(pcm.tobytes())
    except Exception as e:
        print(f"[{label} 錄音錯誤] {e}")


def mix_and_cleanup():
    """用 ffmpeg 把麥克風 + 系統音混成一軌。"""
    print("混音中…")
    cmd = [
        "ffmpeg", "-y",
        "-i", mic_wav,
        "-i", sys_wav,
        "-filter_complex", "amix=inputs=2:duration=longest:normalize=0,dynaudnorm",
        "-ar", str(SR), "-ac", "1",
        final_wav,
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for f in (mic_wav, sys_wav):
        try:
            os.remove(f)
        except OSError:
            pass
    print(f"[已存檔] {final_wav}")


def fmt(ms):
    s = int(ms) // 1000
    return f"{s // 60:02d}:{s % 60:02d}"


def transcribe(audio_path, engine):
    """錄完自動轉繁中逐字稿（SenseVoice 可含說話人分離；Breeze 為時間戳分行）。"""
    print("轉逐字稿中…")
    segs = engine.segments(audio_path)
    lines = []
    for start, spk, text in segs:
        if spk is None:
            lines.append(f"[{fmt(start)}] {text}")
        else:
            lines.append(f"[{fmt(start)}] 說話人{spk}：{text}")
    out = "\n".join(lines)

    txt_path = os.path.splitext(audio_path)[0] + ".txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(out)
    print("\n===== 逐字稿 =====")
    print(out)
    print(f"\n[逐字稿已存檔] {txt_path}")


def main():
    engine_name = choose_engine()      # 先選模型（不馬上載入，錄完才載，錄音不等待）

    spk = sc.default_speaker()
    mic = sc.default_microphone()
    loopback = sc.get_microphone(spk.name, include_loopback=True)

    print("=" * 50)
    print("  會議錄音（麥克風 + 電腦輸出）")
    print(f"  麥克風 : {mic.name}")
    print(f"  系統音 : {spk.name}（loopback）")
    print(f"  存檔夾 : {OUT_DIR}")
    print("=" * 50)
    print("\n🔴 開始錄音… 講話 / 開會即可。")
    print("   要停止，回到本視窗按 Enter。\n")

    t1 = threading.Thread(target=record_source, args=(mic, mic_wav, "麥克風"))
    t2 = threading.Thread(target=record_source, args=(loopback, sys_wav, "系統音"))
    t1.start()
    t2.start()

    try:
        input()          # 按 Enter 停止
    except KeyboardInterrupt:
        pass
    stop_event.set()
    print("⏹️  停止錄音。")
    t1.join()
    t2.join()

    mix_and_cleanup()
    if os.path.exists(final_wav):
        engine = load_engine(engine_name, want_speaker=True)
        transcribe(final_wav, engine)


if __name__ == "__main__":
    main()
