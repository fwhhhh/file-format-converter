"""Audio and video conversions backed by the bundled FFmpeg binary."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from ..core.formats import AUDIO_EXTS, VIDEO_EXTS
from ..core.utils import project_root
from .base import CancelledError, Engine, EngineError, Progress

_CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0

VIDEO_OUT = ["mp4", "mkv", "webm", "avi", "mov", "gif"]
AUDIO_OUT = ["mp3", "wav", "flac", "aac", "m4a", "ogg", "opus", "wma"]
SUBTITLE_OUT = ["srt"]

_PRESETS = {
    "high": {
        "crf": 20,
        "vp9": 30,
        "audio": "192k",
        "vorbis_q": 7,
        "gif_fps": 15,
        "gif_width": 800,
        "q": 2,
        "vbitrate": "4M",
    },
    "balanced": {
        "crf": 23,
        "vp9": 34,
        "audio": "160k",
        "vorbis_q": 5,
        "gif_fps": 12,
        "gif_width": 640,
        "q": 3,
        "vbitrate": "2M",
    },
    "small": {
        "crf": 28,
        "vp9": 40,
        "audio": "96k",
        "vorbis_q": 3,
        "gif_fps": 10,
        "gif_width": 480,
        "q": 5,
        "vbitrate": "1M",
    },
}

_AUDIO_CODEC = {
    "mp3": "libmp3lame",
    "wav": "pcm_s16le",
    "flac": "flac",
    "aac": "aac",
    "m4a": "aac",
    "ogg": "libvorbis",
    "opus": "libopus",
    "wma": "wmav2",
}

_TOOL_CACHE: dict[str, str | None] = {}


def _find_tool(name: str) -> str | None:
    if name in _TOOL_CACHE:
        return _TOOL_CACHE[name]
    exe = name + (".exe" if os.name == "nt" else "")
    roots = [project_root()]
    if getattr(sys, "frozen", False):
        roots.append(Path(sys.executable).resolve().parent)
    found = None
    for root in roots:
        candidate = root / "vendor" / "ffmpeg" / "bin" / exe
        if candidate.exists():
            found = str(candidate)
            break
    if found is None:
        found = shutil.which(name)
    _TOOL_CACHE[name] = found
    return found


class MediaEngine(Engine):
    key = "media"
    label_key = "engine_media"

    def __init__(self) -> None:
        self._encoders: set[str] | None = None

    def available(self) -> bool:
        return _find_tool("ffmpeg") is not None

    def targets(self, src_ext: str) -> list[str]:
        if src_ext in VIDEO_EXTS:
            result = [fmt for fmt in VIDEO_OUT if fmt != src_ext]
            result.extend(AUDIO_OUT)
            result.extend(SUBTITLE_OUT)
            return result
        if src_ext in AUDIO_EXTS:
            return [fmt for fmt in AUDIO_OUT if fmt != src_ext]
        return []

    # ---------------------------------------------------------------- probe

    def probe(self, path: Path) -> dict:
        ffprobe = _find_tool("ffprobe")
        if not ffprobe:
            return {}
        command = [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration:stream=codec_type,width,height",
            "-of",
            "json",
            str(path),
        ]
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
                creationflags=_CREATE_NO_WINDOW,
            )
        except (OSError, subprocess.SubprocessError):
            return {}
        if completed.returncode != 0:
            return {}
        try:
            data = json.loads(completed.stdout or "{}")
        except json.JSONDecodeError:
            return {}
        meta: dict = {}
        try:
            duration = data.get("format", {}).get("duration")
            if duration is not None:
                meta["duration"] = float(duration)
        except (TypeError, ValueError):
            pass
        audio_tracks = 0
        subtitle_tracks = 0
        for stream in data.get("streams", []):
            codec_type = stream.get("codec_type")
            if codec_type == "audio":
                audio_tracks += 1
            elif codec_type == "subtitle":
                subtitle_tracks += 1
            if codec_type == "video" and "width" not in meta:
                if stream.get("width"):
                    meta["width"] = stream.get("width")
                if stream.get("height"):
                    meta["height"] = stream.get("height")
        if audio_tracks:
            meta["audio_tracks"] = audio_tracks
        if subtitle_tracks:
            meta["subtitle_tracks"] = subtitle_tracks
        return meta

    # ----------------------------------------------------------- conversion

    def convert(
        self,
        src: Path,
        dst: Path,
        options: dict,
        progress: Progress | None = None,
    ) -> None:
        ffmpeg = _find_tool("ffmpeg")
        if not ffmpeg:
            raise EngineError("FFmpeg was not found")
        cancel_event = options.get("cancel_event")
        if cancel_event is not None and cancel_event.is_set():
            raise CancelledError()
        source_ext = str(
            options.get("source_format") or src.suffix.lower().lstrip(".")
        )
        target = str(options.get("target_format") or dst.suffix.lower().lstrip("."))
        video_source = source_ext in VIDEO_EXTS
        try:
            audio_index = max(0, int(options.get("audio_track", 0)))
        except (TypeError, ValueError):
            audio_index = 0
        try:
            subtitle_index = max(0, int(options.get("subtitle_track", 0)))
        except (TypeError, ValueError):
            subtitle_index = 0
        if video_source and target in SUBTITLE_OUT:
            self._extract_subtitle(src, dst, subtitle_index, progress)
            return
        if video_source and target in AUDIO_OUT:
            counts = self.probe(src)
            audio_tracks = int(counts.get("audio_tracks", 0))
            if audio_tracks and audio_index >= audio_tracks:
                raise EngineError(
                    f"Audio track {audio_index + 1} does not exist "
                    f"(this file has {audio_tracks})"
                )
        preset_name = str(options.get("preset", "balanced"))
        preset = _PRESETS.get(preset_name, _PRESETS["balanced"])
        duration = self._duration(src)
        if cancel_event is not None and cancel_event.is_set():
            raise CancelledError()

        command = [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-nostdin",
            "-loglevel",
            "error",
            "-progress",
            "pipe:1",
            "-i",
            str(src),
        ]
        if video_source and target in VIDEO_OUT and target != "gif":
            command.extend(
                ["-map", "0:v:0", "-map", f"0:a:{audio_index}?"]
            )
        elif video_source and target in AUDIO_OUT:
            command.extend(["-map", f"0:a:{audio_index}"])
        command.extend(self._codec_args(target, preset, options))
        command.append(str(dst))

        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=_CREATE_NO_WINDOW,
            )
        except OSError as exc:
            raise EngineError(str(exc)) from exc

        last_fraction = 0.0
        assert process.stdout is not None
        for line in process.stdout:
            if cancel_event is not None and cancel_event.is_set():
                process.kill()
                try:
                    process.wait(timeout=5)
                except Exception:
                    pass
                raise CancelledError()
            line = line.strip()
            if not line.startswith("out_time_us="):
                continue
            try:
                microseconds = int(line.split("=", 1)[1])
            except (IndexError, ValueError):
                continue
            if microseconds < 0 or not duration:
                continue
            fraction = min(0.99, microseconds / (duration * 1_000_000))
            if fraction > last_fraction + 0.01:
                last_fraction = fraction
                if progress is not None:
                    progress(fraction)
        error_text = ""
        if process.stderr is not None:
            error_text = process.stderr.read()
        return_code = process.wait()
        if cancel_event is not None and cancel_event.is_set():
            raise CancelledError()
        if return_code != 0:
            message = (error_text or "").strip()
            if not message:
                message = f"FFmpeg exited with code {return_code}"
            raise EngineError(message[-1200:])
        if progress is not None:
            progress(1.0)

    def _duration(self, src: Path) -> float | None:
        meta = self.probe(src)
        value = meta.get("duration")
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _scale_filter(self, options: dict) -> str:
        try:
            height = int(options.get("video_height", 0))
        except (TypeError, ValueError):
            height = 0
        if height > 0:
            return f"scale=-2:'trunc(min(ih,{height})/2)*2'"
        return "scale=trunc(iw/2)*2:trunc(ih/2)*2"

    def _extract_subtitle(
        self,
        src: Path,
        dst: Path,
        index: int,
        progress: Progress | None,
    ) -> None:
        ffmpeg = _find_tool("ffmpeg")
        if not ffmpeg:
            raise EngineError("FFmpeg was not found")
        counts = self.probe(src)
        subtitle_tracks = int(counts.get("subtitle_tracks", 0))
        if subtitle_tracks and index >= subtitle_tracks:
            raise EngineError(
                f"Subtitle track {index + 1} does not exist "
                f"(this file has {subtitle_tracks})"
            )
        command = [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-nostdin",
            "-loglevel",
            "error",
            "-i",
            str(src),
            "-map",
            f"0:s:{index}",
            "-c:s",
            "srt",
            str(dst),
        ]
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=300,
                creationflags=_CREATE_NO_WINDOW,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise EngineError(str(exc)) from exc
        if (
            completed.returncode != 0
            or not dst.exists()
            or dst.stat().st_size == 0
        ):
            message = (completed.stderr or "").strip()
            raise EngineError(message[-1200:] or "No subtitle track found")
        if progress is not None:
            progress(1.0)

    def _codec_args(self, target: str, preset: dict, options: dict) -> list[str]:
        if target in ("mp4", "mov", "mkv"):
            return self._video_h264_args(target, preset, options)
        if target == "webm":
            args = [
                "-c:v",
                "libvpx-vp9",
                "-b:v",
                "0",
                "-crf",
                str(preset["vp9"]),
                "-c:a",
                "libopus",
                "-b:a",
                preset["audio"],
                "-vf",
                self._scale_filter(options),
            ]
            return args
        if target == "avi":
            return [
                "-c:v",
                "mpeg4",
                "-q:v",
                str(preset["q"]),
                "-c:a",
                "libmp3lame",
                "-b:a",
                preset["audio"],
                "-vf",
                self._scale_filter(options),
            ]
        if target == "gif":
            filter_graph = (
                f"fps={preset['gif_fps']},"
                f"scale='min({preset['gif_width']},iw)':-1:flags=lanczos,"
                "split[a][b];[a]palettegen[p];[b][p]paletteuse"
            )
            return ["-filter_complex", filter_graph, "-loop", "0"]
        return self._audio_args(target, preset)

    def _video_h264_args(
        self,
        target: str,
        preset: dict,
        options: dict,
    ) -> list[str]:
        encoders = self._available_encoders()
        if "libx264" in encoders:
            video = [
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                str(preset["crf"]),
                "-pix_fmt",
                "yuv420p",
            ]
        elif "h264_mf" in encoders:
            video = ["-c:v", "h264_mf", "-b:v", preset["vbitrate"], "-pix_fmt", "yuv420p"]
        elif "libopenh264" in encoders:
            video = ["-c:v", "libopenh264", "-b:v", preset["vbitrate"], "-pix_fmt", "yuv420p"]
        else:
            video = ["-c:v", "mpeg4", "-q:v", str(preset["q"])]
        args = video + [
            "-c:a",
            "aac",
            "-b:a",
            preset["audio"],
            "-vf",
            self._scale_filter(options),
        ]
        if target == "mp4":
            args.extend(["-movflags", "+faststart"])
        return args

    def _audio_args(self, target: str, preset: dict) -> list[str]:
        codec = _AUDIO_CODEC.get(target)
        if codec is None:
            raise EngineError(f"Unsupported audio target: {target}")
        args = ["-vn", "-c:a", codec]
        if codec == "libvorbis":
            # libvorbis rejects high fixed bitrates at low sample rates,
            # so use its VBR quality scale instead.
            args.extend(["-q:a", str(preset["vorbis_q"])])
        elif codec not in ("flac", "pcm_s16le"):
            args.extend(["-b:a", preset["audio"]])
        return args

    def _available_encoders(self) -> set[str]:
        if self._encoders is not None:
            return self._encoders
        encoders: set[str] = set()
        ffmpeg = _find_tool("ffmpeg")
        if ffmpeg:
            try:
                completed = subprocess.run(
                    [ffmpeg, "-hide_banner", "-encoders"],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=30,
                    creationflags=_CREATE_NO_WINDOW,
                )
                for line in completed.stdout.splitlines():
                    match = re.match(r"^\s*[VAS][A-Z.]{5}\s+(\S+)", line)
                    if match:
                        encoders.add(match.group(1))
            except (OSError, subprocess.SubprocessError):
                pass
        self._encoders = encoders
        return encoders
