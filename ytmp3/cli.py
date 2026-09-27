"""コマンドライン版: ytmp3 URL [URL ...] [-o DIR] [-b 192] [--start 1:00 --end 2:30] [--video -r 1080]"""

from __future__ import annotations

import argparse
import sys

from .core import BITRATES, RESOLUTIONS, YtMp3Error, download_mp3, parse_time


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="ytmp3", description="YouTube の音声を MP3 で（--video なら動画を MP4 で）保存します。"
    )
    parser.add_argument("urls", nargs="+", metavar="URL", help="動画またはプレイリストの URL")
    parser.add_argument("-o", "--output", default=".", help="保存先フォルダ（既定: カレント）")
    parser.add_argument("-b", "--bitrate", default="192", choices=BITRATES, help="kbps（既定: 192）")
    parser.add_argument("--start", help="切り出し開始 (例: 1:23, 01:02:03, 83.5)")
    parser.add_argument("--end", help="切り出し終了 (例: 2:45)")
    parser.add_argument("--video", action="store_true", help="MP3 ではなく動画を MP4 で保存する")
    parser.add_argument(
        "-r", "--resolution", default="best", choices=RESOLUTIONS,
        help="--video 時の最大画質（既定: best。H.264 で取れる範囲の最高画質）",
    )
    parser.add_argument("--playlist", action="store_true", help="プレイリスト全体を処理する")
    parser.add_argument("-q", "--quiet", action="store_true", help="進捗表示を抑える")
    args = parser.parse_args(argv)

    try:
        start = parse_time(args.start)
        end = parse_time(args.end)
    except YtMp3Error as exc:
        parser.error(str(exc))

    failed = 0
    for url in args.urls:
        try:
            files = download_mp3(
                url, args.output, args.bitrate, start, end, args.playlist,
                quiet=args.quiet, video=args.video, resolution=args.resolution,
            )
        except YtMp3Error as exc:
            print(f"失敗: {url}\n  {exc}", file=sys.stderr)
            failed += 1
            continue
        for f in files:
            print(f"保存: {f}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
