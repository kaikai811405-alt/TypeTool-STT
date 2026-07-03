import sys
import os
sys.stdout.reconfigure(encoding="utf-8")

from asr_engine import choose_engine, load_engine


def fmt(ms):
    s = int(ms) // 1000
    return f"{s // 60:02d}:{s % 60:02d}"


def transcribe(audio_path, engine):
    segs = engine.segments(audio_path)
    lines = []
    for start, spk, text in segs:
        if spk is None:
            lines.append(f"[{fmt(start)}] {text}")        # 無說話人（如 Breeze）
        else:
            lines.append(f"[{fmt(start)}] 說話人{spk}：{text}")
    out = "\n".join(lines)
    print(out)

    out_path = os.path.splitext(audio_path)[0] + "_說話人.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"\n[已存檔] {out_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python transcribe_speaker.py <音檔路徑>")
        sys.exit(1)
    eng = load_engine(choose_engine(), want_speaker=True)
    transcribe(sys.argv[1], eng)
