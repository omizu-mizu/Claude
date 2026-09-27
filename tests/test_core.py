import pytest

from ytmp3.core import YtMp3Error, build_options, format_time, parse_time


@pytest.mark.parametrize(
    "text, expected",
    [("90", 90), ("1:30", 90), ("01:02:03", 3723), ("75.5", 75.5), ("0:00", 0), (" 2:05 ", 125)],
)
def test_parse_time(text, expected):
    assert parse_time(text) == expected


@pytest.mark.parametrize("text", [None, "", "   "])
def test_parse_time_empty(text):
    assert parse_time(text) is None


@pytest.mark.parametrize("text", ["abc", "1:60", "1:2:3:4", "-5", "1::2"])
def test_parse_time_invalid(text):
    with pytest.raises(YtMp3Error):
        parse_time(text)


def test_format_time():
    assert format_time(83) == "1-23"
    assert format_time(3723) == "1-02-03"


def test_build_options_no_range(tmp_path):
    opts = build_options(tmp_path, "320")
    assert "download_ranges" not in opts
    assert opts["postprocessors"][0]["preferredquality"] == "320"
    assert opts["outtmpl"].endswith("%(title)s.%(ext)s")
    assert opts["noplaylist"] is True


def test_build_options_range(tmp_path):
    opts = build_options(tmp_path, start=60, end=150)
    ranges = list(opts["download_ranges"]({}, None))
    assert ranges == [{"start_time": 60, "end_time": 150}]
    assert "[1-00_2-30]" in opts["outtmpl"]


def test_build_options_start_only(tmp_path):
    opts = build_options(tmp_path, start=30)
    ranges = list(opts["download_ranges"]({}, None))
    assert ranges[0]["start_time"] == 30
    assert "[0-30_end]" in opts["outtmpl"]


def test_build_options_invalid(tmp_path):
    with pytest.raises(YtMp3Error):
        build_options(tmp_path, start=10, end=5)
    with pytest.raises(YtMp3Error):
        build_options(tmp_path, bitrate="999")


def test_build_options_audio_default(tmp_path):
    opts = build_options(tmp_path)
    assert opts["format"] == "bestaudio/best"
    keys = [pp["key"] for pp in opts["postprocessors"]]
    assert keys == ["FFmpegExtractAudio", "FFmpegMetadata", "EmbedThumbnail"]
    assert "merge_output_format" not in opts


def test_build_options_video(tmp_path):
    opts = build_options(tmp_path, video=True, resolution="720")
    assert opts["merge_output_format"] == "mp4"
    assert opts["format_sort"] == ["vcodec:h264", "res:720", "acodec:m4a"]
    keys = [pp["key"] for pp in opts["postprocessors"]]
    assert "FFmpegExtractAudio" not in keys


def test_build_options_video_best(tmp_path):
    opts = build_options(tmp_path, video=True)
    assert opts["format_sort"][1] == "res"


def test_build_options_invalid_resolution(tmp_path):
    with pytest.raises(YtMp3Error):
        build_options(tmp_path, video=True, resolution="4k")
