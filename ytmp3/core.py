"""ダウンロードと MP3 / MP4 変換の本体。CLI と Web UI の両方から使う。"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Callable, Optional

import yt_dlp
from yt_dlp.utils import download_range_func

BITRATES = ("128", "192", "256", "320")
RESOLUTIONS = ("best", "1080", "720", "480", "360")


class YtMp3Error(Exception):
    """利用者に見せるエラー。"""


def parse_time(value: Optional[str]) -> Optional[float]:
    """'90', '1:30', '1:02:03', '75.5' のような文字列を秒に変換する。空なら None。"""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    parts = text.split(":")
    if len(parts) > 3:
        raise YtMp3Error(f"時刻の形式が不正です: {value!r}")
    try:
        nums = [float(p) for p in parts]
    except ValueError:
        raise YtMp3Error(f"時刻の形式が不正です: {value!r}") from None
    if any(n < 0 for n in nums) or any(n >= 60 for n in nums[1:]):
        raise YtMp3Error(f"時刻の形式が不正です: {value!r}")
    seconds = 0.0
    for n in nums:
        seconds = seconds * 60 + n
    return seconds


def format_time(seconds: float) -> str:
    """秒を 'H-MM-SS' / 'M-SS' 形式（ファイル名用）にする。"""
    total = int(seconds)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h}-{m:02d}-{s:02d}" if h else f"{m}-{s:02d}"


def check_ffmpeg() -> None:
    if shutil.which("ffmpeg") is None:
        raise YtMp3Error(
            "ffmpeg が見つかりません。README の手順でインストールし、PATH を通してください。"
        )


def build_options(
    out_dir: Path,
    bitrate: str = "192",
    start: Optional[float] = None,
    end: Optional[float] = None,
    playlist: bool = False,
    progress_hook: Optional[Callable[[dict], None]] = None,
    quiet: bool = False,
    video: bool = False,
    resolution: str = "best",
) -> dict:
    if bitrate not in BITRATES:
        raise YtMp3Error(f"ビットレートは {', '.join(BITRATES)} から選んでください。")
    if resolution not in RESOLUTIONS:
        raise YtMp3Error(f"画質は {', '.join(RESOLUTIONS)} から選んでください。")
    if start is not None and end is not None and end <= start:
        raise YtMp3Error("終了時刻は開始時刻より後にしてください。")

    template = "%(title)s"
    opts: dict = {
        "noplaylist": not playlist,
        "windowsfilenames": True,
        "quiet": quiet,
        "no_warnings": quiet,
        "noprogress": quiet,
        "writethumbnail": True,
        "postprocessors": [
            {"key": "FFmpegMetadata", "add_metadata": True},
            {"key": "EmbedThumbnail"},
        ],
    }

    if video:
        # どの PC・ソフトでも再生できるよう、画質より H.264 + AAC を優先する
        opts["format"] = "bv*+ba/b"
        opts["format_sort"] = [
            "vcodec:h264",
            "res" if resolution == "best" else f"res:{resolution}",
            "acodec:m4a",
        ]
        opts["merge_output_format"] = "mp4"
    else:
        opts["format"] = "bestaudio/best"
        opts["postprocessors"].insert(
            0,
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": bitrate,
            },
        )

    if start is not None or end is not None:
        s = start or 0.0
        e = end if end is not None else float("inf")
        opts["download_ranges"] = download_range_func(None, [(s, e)])
        opts["force_keyframes_at_cuts"] = True
        suffix = f" [{format_time(s)}_{format_time(e) if end is not None else 'end'}]"
        template += suffix

    opts["outtmpl"] = str(out_dir / f"{template}.%(ext)s")
    if progress_hook is not None:
        opts["progress_hooks"] = [progress_hook]
    return opts


def download_mp3(
    url: str,
    out_dir: str | Path = ".",
    bitrate: str = "192",
    start: Optional[float] = None,
    end: Optional[float] = None,
    playlist: bool = False,
    progress_hook: Optional[Callable[[dict], None]] = None,
    quiet: bool = False,
    video: bool = False,
    resolution: str = "best",
) -> list[Path]:
    """URL の音声を MP3（video=True なら動画を MP4）で保存し、作成したファイルのパスを返す。"""
    check_ffmpeg()
    out = Path(out_dir).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)

    created: list[Path] = []

    def _pp_hook(d: dict) -> None:
        if d.get("status") == "finished" and d.get("postprocessor") == "MoveFiles":
            path = d.get("info_dict", {}).get("filepath")
            if path:
                created.append(Path(path))

    opts = build_options(
        out, bitrate, start, end, playlist, progress_hook, quiet, video, resolution
    )
    opts["postprocessor_hooks"] = [_pp_hook]

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
    except yt_dlp.utils.DownloadError as exc:
        raise YtMp3Error(str(exc)) from exc

    # 同じファイルが複数回報告されることがあるので重複を除く
    ext = ".mp4" if video else ".mp3"
    return list(dict.fromkeys(p.with_suffix(ext) for p in created))
