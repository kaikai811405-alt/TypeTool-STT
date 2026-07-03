import sys
import os
sys.stdout.reconfigure(encoding="utf-8")

from asr_engine import choose_engine, load_engine


def transcribe(audio_path, engine):
    text = engine.text(audio_path)
    print(text)
    out_path = os.path.splitext(audio_path)[0] + ".txt"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"\n[已存檔] {out_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python transcribe_file.py <音檔路徑>")
        sys.exit(1)
    eng = load_engine(choose_engine())
    transcribe(sys.argv[1], eng)
