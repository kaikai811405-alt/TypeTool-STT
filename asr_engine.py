"""統一辨識後端：SenseVoice（funasr）與 Breeze-ASR-25（transformers/Whisper）。

對外介面：
    engine = load_engine(name, want_speaker=False, short=False)
    engine.text(path)       -> str                       純文字（已轉繁中）
    engine.segments(path)   -> [(start_ms, spk, text)]    spk 為 None 表示不支援說話人

啟動選單：
    name = choose_engine()  # 互動式，回傳 "sensevoice" 或 "breeze"
"""
import sys
import os

# ---------- 自訂取代字典 ----------
# dict.txt 每行「錯詞=正確詞」，# 開頭為註解。辨識後自動替換（四個工具共用）。
_DICT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dict.txt")


def _load_dict():
    pairs = []
    if os.path.exists(_DICT_PATH):
        with open(_DICT_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                old, new = line.split("=", 1)
                if old.strip():
                    pairs.append((old.strip(), new.strip()))
    return pairs


_DICT = _load_dict()


def apply_dict(text):
    for old, new in _DICT:
        text = text.replace(old, new)
    return text


MODELS = {
    "1": ("sensevoice", "SenseVoice（快，通用，支援說話人分離）"),
    "2": ("breeze", "Breeze-ASR-25（準，台灣中英夾雜，較慢，無說話人分離）"),
}


def choose_engine(default="breeze"):
    print("=" * 50)
    print("  選擇辨識模型：")
    print("   1) SenseVoice     — 快、通用、可分辨說話人")
    print("   2) Breeze-ASR-25  — 台灣中英夾雜最準，較慢，不分說話人")
    print("=" * 50)
    c = input("輸入 1 或 2（直接按 Enter 用 2）：").strip()
    name = MODELS.get(c, ("breeze", ""))[0]
    print(f"→ 使用 {name}\n")
    return name


# ---------- SenseVoice ----------
class SenseVoiceEngine:
    def __init__(self, want_speaker=False, short=False):
        import opencc
        from funasr import AutoModel
        self._cc = opencc.OpenCC("s2twp")
        self.want_speaker = want_speaker
        kw = dict(model="iic/SenseVoiceSmall", device="cuda:0", disable_update=True)
        if not short:
            kw["vad_model"] = "fsmn-vad"      # 短句即時輸入不掛 VAD，降延遲
        if want_speaker:
            kw["vad_model"] = "fsmn-vad"
            kw["spk_model"] = "cam++"
        print("載入 SenseVoice…")
        self.model = AutoModel(**kw)

    def _post(self, s):
        from funasr.utils.postprocess_utils import rich_transcription_postprocess
        return apply_dict(self._cc.convert(rich_transcription_postprocess(s)))

    def text(self, path):
        res = self.model.generate(input=path, language="auto", use_itn=True, batch_size_s=300)
        return self._post(res[0]["text"]).strip()

    def segments(self, path):
        res = self.model.generate(input=path, language="auto", use_itn=True, batch_size_s=300)
        si = res[0].get("sentence_info") if self.want_speaker else None
        if si:
            return [(seg.get("start", 0), seg.get("spk", 0), self._post(seg.get("sentence", ""))) for seg in si]
        return [(0, None, self._post(res[0]["text"]))]


# ---------- Breeze-ASR-25 ----------
class BreezeEngine:
    def __init__(self, want_speaker=False, short=False):
        import torch
        from transformers import (WhisperProcessor, WhisperForConditionalGeneration,
                                   AutomaticSpeechRecognitionPipeline)
        if want_speaker:
            print("⚠️  Breeze 不支援說話人分離，將改以時間戳分行（不標說話人）。")
        self.want_speaker = want_speaker
        print("載入 Breeze-ASR-25…（首次會下載約 3GB）")
        repo = "MediaTek-Research/Breeze-ASR-25"
        proc = WhisperProcessor.from_pretrained(repo)
        model = WhisperForConditionalGeneration.from_pretrained(
            repo, torch_dtype=torch.float16).to("cuda").eval()
        self.pipe = AutomaticSpeechRecognitionPipeline(
            model=model, tokenizer=proc.tokenizer,
            feature_extractor=proc.feature_extractor,
            chunk_length_s=0, device=0)   # 0=長音檔連續解碼，官方建議

    def _load(self, path):
        # 用 ffmpeg 解碼任何格式 → 16k 單聲道 float32（避開 torchaudio/torchcodec 後端問題）
        import subprocess
        import numpy as np
        cmd = ["ffmpeg", "-i", path, "-f", "f32le", "-ac", "1",
               "-ar", "16000", "-v", "quiet", "pipe:1"]
        raw = subprocess.run(cmd, capture_output=True).stdout
        return np.frombuffer(raw, dtype=np.float32).copy()

    # no_repeat_ngram_size：擋掉 Whisper 在短音檔常見的「整句重複」幻覺
    _GEN = {"language": "zh", "no_repeat_ngram_size": 3}

    def text(self, path):
        # 純文字不需時間戳；關掉可再降低短音檔重複機率
        out = self.pipe(self._load(path), return_timestamps=False,
                        generate_kwargs=self._GEN)
        return apply_dict(out["text"].strip())   # 原生繁中，不套 OpenCC

    def segments(self, path):
        out = self.pipe(self._load(path), return_timestamps=True,
                        generate_kwargs=self._GEN)
        segs = []
        for c in out.get("chunks", []):
            start = c.get("timestamp", (0,))[0] or 0
            segs.append((int(start * 1000), None, apply_dict(c["text"].strip())))
        if not segs:
            segs = [(0, None, apply_dict(out["text"].strip()))]
        return segs


def load_engine(name, want_speaker=False, short=False):
    if name == "breeze":
        return BreezeEngine(want_speaker=want_speaker, short=short)
    return SenseVoiceEngine(want_speaker=want_speaker, short=short)
