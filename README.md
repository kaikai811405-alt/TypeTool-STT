# TypeTool-STT

本機語音轉文字工具（Windows），全程**離線在地運算**，輸出**繁體中文（台灣用詞）**。
支援兩個辨識模型、四種功能，安裝腳本會**自動偵測顯卡**（有 NVIDIA 用 GPU，沒有就用 CPU）。

---

## 功能

| 功能 | 啟動方式 | 說明 |
|---|---|---|
| 🎤 語音輸入 | 雙擊 `語音輸入.bat` | 按住 **Alt+Ctrl** 講話、放開，文字自動貼到游標處 |
| 🔴 錄會議 | 雙擊 `錄會議.bat` | 同時錄**麥克風 + 電腦喇叭輸出**（Teams/Meet/電話），按 Enter 停 → 自動轉逐字稿 |
| 📄 轉逐字稿 | 把音檔拖到 `轉逐字稿_拖曳音檔到此.bat` | wav / mp3 / m4a / mp4 皆可，同名 `.txt` 輸出 |
| 👥 說話人分離 | 把音檔拖到 `說話人分離_拖曳音檔到此.bat` | 標記「說話人1 / 2 / 3…」（僅 SenseVoice） |

---

## 兩個模型（每次啟動時選 1 或 2）

| | 1) SenseVoice | 2) Breeze-ASR-25 |
|---|---|---|
| 速度 | 極快 | 較慢（每句多等約 0.5–1 秒） |
| 繁中 | OpenCC 轉台灣正體 | **原生台灣繁中** |
| 強項 | 通用、低延遲、可分辨說話人 | **台灣口語、中英夾雜** |
| 說話人分離 | ✅ | ❌（改時間戳分行） |
| VRAM（GPU） | ~1GB | ~3.3GB |

> 一般會議、要分辨誰在講 → 選 1；中英夾雜多、要最準台灣口語 → 選 2（首次用會下載約 3GB）。

---

## 安裝

### 需求
- **Windows 10 / 11**
- 有 [winget](https://learn.microsoft.com/windows/package-manager/winget/)（Win11 內建）與網路連線
- NVIDIA 顯卡（選配）：有的話速度快很多；沒有也能跑（CPU，較慢，Breeze 會很慢）

### 步驟
1. 下載本專案（擇一）：
   - `git clone https://github.com/<你的帳號>/TypeTool-STT.git`
   - 或按綠色 **Code → Download ZIP** 解壓縮
2. 進入資料夾，**雙擊 `install.bat`**
3. 腳本會自動：裝 Python 3.11 → ffmpeg → 建 venv → **偵測顯卡選對 PyTorch** → 裝所有套件
4. 看到「安裝完成！」即可開始用（模型於首次使用時自動下載，需網路）

> 安裝完成後整個資料夾可自由搬移、改名，`.bat` 會自己找同資料夾的 `venv`。

---

## 自訂取代字典

專業術語常被聽錯？編輯 `dict.txt`，每行「錯詞=正確詞」：
```
快樂=Creo
安色斯=Ansys
```
辨識後自動替換，四個功能都套用。改完存檔、重開工具即生效。

---

## 常見問題

| 問題 | 處理 |
|---|---|
| 沒有 NVIDIA 顯卡能用嗎？ | 可以，`install.bat` 會自動裝 CPU 版。建議以 SenseVoice 為主，Breeze 在 CPU 上很慢 |
| CUDA 版裝好但跑不動 | 顯卡驅動太舊 → 更新 NVIDIA 驅動；或改用 CPU（把 install.bat 的 index 改 `.../whl/cpu` 重裝） |
| 語音輸入小聲被略過 | 調低 `voice_input.py` 裡的 `VAD_THRESHOLD`（0.5 → 0.3） |
| 錄會議只錄到單邊 | 確認 Windows 預設播放/錄音裝置 |
| 中文變亂碼 | 腳本已強制 UTF-8，若異常請開 issue |

更完整說明見 [`使用說明書.md`](使用說明書.md)。

---

## 關鍵版本（勿亂升級）
- Python 3.11、PyTorch 2.9.1、torchaudio 2.9.1
- funasr 1.3.14、**transformers 4.46.3（不可升 5.x，會打亂輸出）**、opencc、soundcard、silero-vad

## 授權
程式碼 MIT。第三方模型（SenseVoice、Breeze-ASR-25）各有授權，見 [`LICENSE`](LICENSE)。
