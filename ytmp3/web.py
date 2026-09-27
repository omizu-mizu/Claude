"""ブラウザ版: ytmp3-web で起動し http://127.0.0.1:8000 を開く。"""

from __future__ import annotations

import argparse
import threading
import uuid
import webbrowser
from pathlib import Path

from flask import Flask, abort, jsonify, render_template, request, send_file

from .core import BITRATES, RESOLUTIONS, YtMp3Error, check_ffmpeg, download_mp3, parse_time

DEFAULT_OUTPUT = Path.home() / "Music" / "ytmp3"


def create_app(output_dir: Path = DEFAULT_OUTPUT) -> Flask:
    app = Flask(__name__)
    jobs: dict[str, dict] = {}
    lock = threading.Lock()

    def update(job_id: str, **fields) -> None:
        with lock:
            jobs[job_id].update(fields)

    def run_job(
        job_id: str, url: str, bitrate: str, start, end, playlist: bool,
        video: bool, resolution: str,
    ) -> None:
        def hook(d: dict) -> None:
            if d.get("status") == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate")
                done = d.get("downloaded_bytes") or 0
                pct = round(done * 100 / total, 1) if total else None
                title = d.get("info_dict", {}).get("title")
                update(job_id, status="downloading", percent=pct, title=title)
            elif d.get("status") == "finished":
                update(job_id, status="converting", percent=100)

        try:
            files = download_mp3(
                url, output_dir, bitrate, start, end, playlist, hook,
                quiet=True, video=video, resolution=resolution,
            )
        except YtMp3Error as exc:
            update(job_id, status="error", error=str(exc))
            return
        except Exception as exc:  # 想定外のエラーも画面に出す
            update(job_id, status="error", error=f"{type(exc).__name__}: {exc}")
            return
        update(job_id, status="done", files=[f.name for f in files])

    @app.get("/")
    def index():
        return render_template(
            "index.html", bitrates=BITRATES, resolutions=RESOLUTIONS, output_dir=str(output_dir)
        )

    @app.post("/api/jobs")
    def create_job():
        data = request.get_json(silent=True) or {}
        url = (data.get("url") or "").strip()
        if not url:
            return jsonify(error="URL を入力してください。"), 400
        bitrate = str(data.get("bitrate") or "192")
        video = bool(data.get("video"))
        resolution = str(data.get("resolution") or "best")
        try:
            if bitrate not in BITRATES:
                raise YtMp3Error("ビットレートが不正です。")
            if resolution not in RESOLUTIONS:
                raise YtMp3Error("画質が不正です。")
            start = parse_time(data.get("start"))
            end = parse_time(data.get("end"))
            if start is not None and end is not None and end <= start:
                raise YtMp3Error("終了時刻は開始時刻より後にしてください。")
            check_ffmpeg()
        except YtMp3Error as exc:
            return jsonify(error=str(exc)), 400

        job_id = uuid.uuid4().hex
        with lock:
            jobs[job_id] = {
                "id": job_id, "url": url, "status": "queued", "percent": None,
                "title": None, "files": [], "error": None,
            }
        threading.Thread(
            target=run_job,
            args=(job_id, url, bitrate, start, end, bool(data.get("playlist")), video, resolution),
            daemon=True,
        ).start()
        return jsonify(id=job_id), 202

    @app.get("/api/jobs/<job_id>")
    def get_job(job_id: str):
        with lock:
            job = jobs.get(job_id)
            if job is None:
                abort(404)
            return jsonify(dict(job))

    @app.get("/api/jobs/<job_id>/files/<int:index>")
    def get_file(job_id: str, index: int):
        with lock:
            job = jobs.get(job_id)
            names = list(job["files"]) if job else []
        if not 0 <= index < len(names):
            abort(404)
        path = (output_dir / names[index]).resolve()
        if path.parent != output_dir.resolve() or not path.is_file():
            abort(404)
        return send_file(path, as_attachment=True, download_name=path.name)

    return app


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="ytmp3-web", description="ytmp3 の Web UI を起動します。")
    parser.add_argument("--host", default="127.0.0.1", help="LAN から使うときは 0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("-o", "--output", default=str(DEFAULT_OUTPUT), help="保存先フォルダ")
    parser.add_argument("--no-browser", action="store_true", help="ブラウザを自動で開かない")
    args = parser.parse_args(argv)

    output = Path(args.output).expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    app = create_app(output)
    url = f"http://127.0.0.1:{args.port}"
    print(f"保存先: {output}\n{url} を開いてください（終了は Ctrl+C）")
    if not args.no_browser:
        threading.Timer(1.0, webbrowser.open, args=(url,)).start()
    app.run(host=args.host, port=args.port, threaded=True)


if __name__ == "__main__":
    main()
