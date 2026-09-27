# ytmp3

[yt-dlp](https://github.com/yt-dlp/yt-dlp) を使って YouTube の音声を MP3 で、または動画を MP4 で保存するツールです。
コマンドライン版（`ytmp3`）とブラウザ版（`ytmp3-web`）の2通りで使えます。

- 開始・終了時刻を指定した**区間の切り出し**
- ビットレート指定（128 / 192 / 256 / 320 kbps）
- **MP4（動画）での保存**。画質は 最高 / 1080p / 720p / 480p / 360p から選択
  - どの PC・ソフト（Windows 標準プレーヤー、PowerPoint など）でも再生できるよう、H.264 形式を優先します。そのため YouTube に 4K があっても、多くの場合 1080p が上限になります
  - 指定した画質以下がない場合は、それに最も近い画質になります
- タイトルなどのメタデータとサムネイル（カバー画像）を埋め込み
- プレイリストの一括処理（任意）

> 自分が権利を持つ動画、またはダウンロードが許可されている動画にのみ使ってください。

## セットアップ（Windows）

PowerShell で必要なものを入れます（初回のみ）。

```powershell
winget install Python.Python.3.12
winget install Gyan.FFmpeg
winget install DenoLand.Deno
```

- **ffmpeg** は MP3 への変換と区間の切り出しに必要です。
- **Deno** は最近の yt-dlp が YouTube を処理するときに使う JavaScript ランタイムです。ない場合、一部の動画で失敗することがあります。

インストール後は **PowerShell を開き直して** PATH を反映させてください。次に、このフォルダの `setup.bat` をダブルクリックします（`.venv` を作って ytmp3 をインストールします）。

## 使い方

### ブラウザ版

`start_web.bat` をダブルクリックすると、ブラウザで `http://127.0.0.1:8000` が開きます。

1. URL を貼り付ける
2. 「MP3（音声）」か「MP4（動画）」を選ぶ
3. 必要なら開始・終了時刻を入れる（例: `1:23`、`01:02:03`、`83.5`。片方だけでも可）
4. 音質（MP3）または画質（MP4）を選んで、ボタンを押す

できたファイルは MP3・MP4 とも `%USERPROFILE%\Music\ytmp3` に保存され、画面のリンクからもダウンロードできます。

オプション（`start_web.bat` に続けて指定するか、`ytmp3-web` を直接実行）:

| オプション | 説明 |
|---|---|
| `-o DIR` | 保存先フォルダ |
| `--port 8000` | ポート番号 |
| `--host 0.0.0.0` | 同じ LAN のスマホなどからも使う（Windows ファイアウォールの許可が必要） |
| `--no-browser` | ブラウザを自動で開かない |

### コマンドライン版

`.venv\Scripts\activate` で仮想環境を有効にしてから実行します。

```powershell
# 基本
ytmp3 "https://www.youtube.com/watch?v=XXXXXXXXXXX"

# 1分23秒〜2分45秒だけを 320kbps で、Music フォルダへ
ytmp3 "https://www.youtube.com/watch?v=XXXXXXXXXXX" --start 1:23 --end 2:45 -b 320 -o "$env:USERPROFILE\Music"

# 30秒から最後まで
ytmp3 "https://youtu.be/XXXXXXXXXXX" --start 30

# 動画を MP4 で（H.264 で取れる最高画質）
ytmp3 "https://www.youtube.com/watch?v=XXXXXXXXXXX" --video

# 720p の MP4 で、1分〜1分30秒だけ
ytmp3 "https://www.youtube.com/watch?v=XXXXXXXXXXX" --video -r 720 --start 1:00 --end 1:30

# プレイリスト全体
ytmp3 "https://www.youtube.com/playlist?list=XXXX" --playlist
```

URL は複数並べられます。`ytmp3 -h` でオプション一覧を表示します。

区間を指定すると、ファイル名の末尾に `[1-23_2-45]` のように区間が付きます。

## うまく動かないとき

- **急にダウンロードできなくなった**: YouTube 側の仕様変更が多いので、まず `update.bat` で yt-dlp を最新版にしてください。
- **「ffmpeg が見つかりません」**: `ffmpeg -version` が PowerShell で動くか確認してください。動かなければ PATH が通っていません（PowerShell の開き直し、または PC の再起動）。
- **区間の端が少しずれる**: 切り出し位置で再エンコードしているので通常は正確ですが、元の音声によっては 0.1 秒以下のずれが出ることがあります。

## 開発

```powershell
pip install -e ".[dev]"
pytest
```

構成:

- `ytmp3/core.py` — yt-dlp の呼び出しと時刻の解析（CLI と Web で共通）
- `ytmp3/cli.py` — コマンドライン版
- `ytmp3/web.py`, `ytmp3/templates/index.html` — ブラウザ版（Flask）
