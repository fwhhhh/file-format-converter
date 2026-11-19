from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from app.engines import media as media_module
from app.engines.media import MediaEngine


def _ffmpeg():
    return media_module._find_tool("ffmpeg")


@pytest.mark.skipif(_ffmpeg() is None, reason="FFmpeg is not available")
def test_subtitle_and_audio_track_selection(tmp_path):
    ffmpeg = _ffmpeg()
    assert ffmpeg is not None
    subtitle = tmp_path / "sub.srt"
    subtitle.write_text(
        "1\n00:00:00,000 --> 00:00:01,000\nHello subtitle\n",
        encoding="utf-8",
    )
    source = tmp_path / "multi.mkv"
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "testsrc=duration=1:size=320x240:rate=10",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:duration=1",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=880:duration=1",
            "-f",
            "srt",
            "-i",
            str(subtitle),
            "-map",
            "0:v",
            "-map",
            "1:a",
            "-map",
            "2:a",
            "-map",
            "3:s",
            "-c:v",
            "mpeg4",
            "-q:v",
            "5",
            "-c:a",
            "aac",
            "-c:s",
            "srt",
            "-shortest",
            str(source),
        ],
        check=True,
        creationflags=media_module._CREATE_NO_WINDOW,
    )

    engine = MediaEngine()
    metadata = engine.probe(source)
    assert metadata.get("audio_tracks") == 2
    assert metadata.get("subtitle_tracks") == 1
    assert "srt" in engine.targets("mkv")

    subtitle_out = tmp_path / "out.srt"
    engine.convert(
        source,
        subtitle_out,
        {
            "target_format": "srt",
            "source_format": "mkv",
            "subtitle_track": 0,
        },
    )
    assert "Hello subtitle" in subtitle_out.read_text(encoding="utf-8")

    audio_out = tmp_path / "track2.mp3"
    engine.convert(
        source,
        audio_out,
        {
            "target_format": "mp3",
            "source_format": "mkv",
            "audio_track": 1,
        },
    )
    assert audio_out.exists() and audio_out.stat().st_size > 0

    video_out = tmp_path / "small.mp4"
    engine.convert(
        source,
        video_out,
        {
            "target_format": "mp4",
            "source_format": "mkv",
            "audio_track": 0,
            "video_height": 120,
        },
    )
    small_meta = engine.probe(video_out)
    assert small_meta.get("height") == 120
