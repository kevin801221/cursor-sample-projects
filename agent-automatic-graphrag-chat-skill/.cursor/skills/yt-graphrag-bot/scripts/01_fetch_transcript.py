#!/usr/bin/env python3
"""
Step 1: 從 YouTube 連結擷取逐字稿
=================================
策略（依序 fallback）:
  1. 人工上傳字幕 (CC)          -> 最準確
  2. YouTube 自動產生字幕 (ASR) -> 沒有 CC 也能用
  3. 都沒有 -> 下載音訊，提示改用 faster-whisper 本地轉錄（見 SKILL.md Phase 1 附註）

驗證環境: yt-dlp 2026.07.04 / Python 3.12
用法:
  python 01_fetch_transcript.py "https://www.youtube.com/watch?v=VIDEO_ID" \
      --lang zh-TW zh-Hant zh en --out transcript.json
輸出: JSON，含 video metadata 與帶時間戳的段落列表
  [{"start": 12.3, "end": 15.8, "text": "..."}, ...]
時間戳很重要：後面 RAG 回答時可以引用「影片第幾分幾秒」。
"""
import argparse
import json
import re
import sys
from pathlib import Path

import yt_dlp


def pick_subtitle_lang(available: dict, preferred: list[str]) -> str | None:
    """從可用字幕中挑選最符合偏好的語言代碼（支援前綴比對，如 zh 比對 zh-TW）。"""
    if not available:
        return None
    for want in preferred:
        for lang in available:
            if lang == want or lang.startswith(want + "-") or want.startswith(lang + "-"):
                return lang
    # 都沒中就拿第一個
    return next(iter(available))


def parse_vtt(vtt_text: str) -> list[dict]:
    """解析 WebVTT -> [{start, end, text}]，並去除 ASR 字幕常見的重複行。

    坑 1: YouTube 自動字幕 (ASR) 的 VTT 會有「滾動式重複」——同一句話出現在
          連續兩個 cue 裡。這裡用「與前一句尾端重疊」偵測去重。
    坑 2: cue 內含 <00:00:01.500><c>word</c> 這種 word-level 標記，要先剝掉。
    """
    ts = re.compile(
        r"(\d{2}):(\d{2}):(\d{2})\.(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})\.(\d{3})"
    )
    tag = re.compile(r"<[^>]+>")
    segments: list[dict] = []
    cur_start = cur_end = None
    buf: list[str] = []

    def flush():
        nonlocal cur_start, cur_end, buf
        if cur_start is None:
            return
        text = " ".join(t for t in buf if t).strip()
        text = re.sub(r"\s+", " ", text)
        if text:
            # 去除滾動式重複：新 cue 若完全包含於前一段尾端則略過
            if segments and (text in segments[-1]["text"] or segments[-1]["text"].endswith(text)):
                segments[-1]["end"] = cur_end
            elif segments and text.startswith(segments[-1]["text"]):
                # 新段是前段的延伸 -> 只保留延伸部分
                extra = text[len(segments[-1]["text"]):].strip()
                if extra:
                    segments.append({"start": cur_start, "end": cur_end, "text": extra})
                else:
                    segments[-1]["end"] = cur_end
            else:
                segments.append({"start": cur_start, "end": cur_end, "text": text})
        cur_start = cur_end = None
        buf = []

    for raw in vtt_text.splitlines():
        line = raw.strip()
        m = ts.search(line)
        if m:
            flush()
            h1, m1, s1, ms1, h2, m2, s2, ms2 = map(int, m.groups())
            cur_start = h1 * 3600 + m1 * 60 + s1 + ms1 / 1000
            cur_end = h2 * 3600 + m2 * 60 + s2 + ms2 / 1000
            continue
        if not line or line == "WEBVTT" or line.startswith(("Kind:", "Language:", "NOTE", "STYLE")):
            continue
        if cur_start is not None:
            buf.append(tag.sub("", line).strip())
    flush()
    return segments


def fetch(url: str, preferred_langs: list[str], out_path: Path) -> dict:
    probe_opts = {"skip_download": True, "quiet": True, "no_warnings": True}
    with yt_dlp.YoutubeDL(probe_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    manual = info.get("subtitles") or {}
    auto = info.get("automatic_captions") or {}

    source, lang = None, None
    if (lang := pick_subtitle_lang(manual, preferred_langs)):
        source = "manual"
    elif (lang := pick_subtitle_lang(auto, preferred_langs)):
        source = "auto"

    if source is None:
        print("[!] 此影片沒有任何字幕（含自動字幕）。", file=sys.stderr)
        print("[!] 請改走 whisper 路線：", file=sys.stderr)
        print(f'    yt-dlp -x --audio-format m4a -o audio.m4a "{url}"', file=sys.stderr)
        print("    然後用 faster-whisper 轉錄（見 SKILL.md Phase 1）。", file=sys.stderr)
        sys.exit(2)

    print(f"[*] 使用 {source} 字幕，語言: {lang}")
    dl_opts = {
        "skip_download": True,
        "writesubtitles": source == "manual",
        "writeautomaticsub": source == "auto",
        "subtitleslangs": [lang],
        "subtitlesformat": "vtt",
        "outtmpl": str(out_path.parent / "subs" / "%(id)s"),
        "quiet": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(dl_opts) as ydl:
        ydl.download([url])

    # 先找本次語言的精確檔名，避免撿到上一次跑別的 --lang 留下的舊字幕
    subs_dir = out_path.parent / "subs"
    vtt_files = (list(subs_dir.glob(f"{info['id']}.{lang}.vtt"))
                 or list(subs_dir.glob(f"{info['id']}*.vtt")))
    if not vtt_files:
        print("[!] 字幕下載失敗（可能被 rate limit，稍後重試）", file=sys.stderr)
        sys.exit(3)

    segments = parse_vtt(vtt_files[0].read_text(encoding="utf-8"))
    result = {
        "video_id": info["id"],
        "title": info.get("title"),
        "channel": info.get("channel"),
        "duration": info.get("duration"),
        "url": url,
        "subtitle_source": source,
        "subtitle_lang": lang,
        "segments": segments,
    }
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[✓] {len(segments)} 段字幕已存至 {out_path}")
    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--lang", nargs="+", default=["zh-TW", "zh-Hant", "zh", "en"])
    ap.add_argument("--out", type=Path, default=Path("transcript.json"))
    args = ap.parse_args()
    fetch(args.url, args.lang, args.out)
