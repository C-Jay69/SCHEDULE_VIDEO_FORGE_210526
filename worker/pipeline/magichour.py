"""Magic Hour AI video generation provider.

Wraps the official magic_hour Python SDK so the pipeline can generate real
AI visuals for a video from an existing voiceover track (Audio-to-Video API).

The generated clip's duration matches the supplied audio segment, which lets
the rest of the pipeline burn captions on top with FFmpeg while keeping the
original voiceover intact.
"""

import logging
import os
import subprocess
import tempfile

logger = logging.getLogger(__name__)


class MagicHourError(RuntimeError):
    """Raised when Magic Hour generation fails or is not configured."""


def is_configured() -> bool:
    return bool(os.getenv("MAGIC_HOUR_API_KEY"))


def _ensure_mp3(audio_path: str) -> str:
    """Return an mp3 for the audio file, transcoding if needed.

    Magic Hour's audio-to-video accepts compressed audio (mp3/m4a). Piper
    outputs .wav, so transcode when necessary into a sibling temp file.
    """
    if audio_path.lower().endswith(".mp3"):
        return audio_path
    mp3_path = os.path.join(tempfile.gettempdir(), os.path.basename(audio_path).rsplit(".", 1)[0] + ".mp3")
    cmd = ["ffmpeg", "-y", "-i", audio_path, "-b:a", "192k", mp3_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise MagicHourError(f"Failed to transcode audio to mp3: {result.stderr[-300:]}")
    return mp3_path


def generate_video_from_audio(
    audio_path: str,
    prompt: str,
    output_dir: str,
    end_seconds: float,
    resolution: str = "720p",
    name: str = "VideoForge",
) -> str:
    """Generate AI visuals for a voiceover via Magic Hour audio-to-video.

    Uploads the local audio file, creates the job, waits for completion and
    downloads the result into ``output_dir``.

    Returns the absolute path of the downloaded video.
    """
    api_key = os.getenv("MAGIC_HOUR_API_KEY")
    if not api_key:
        raise MagicHourError("MAGIC_HOUR_API_KEY is not set")

    try:
        from magic_hour import Client
    except ImportError:
        raise MagicHourError("magic_hour package is not installed") from None

    os.makedirs(output_dir, exist_ok=True)

    audio_for_upload = _ensure_mp3(audio_path)

    logger.info("Magic Hour: submitting audio-to-video job (%.1fs, %s)...", end_seconds, resolution)
    client = Client(token=api_key)
    result = client.v1.audio_to_video.generate(
        assets={"audio_file_path": audio_for_upload},
        start_seconds=0,
        end_seconds=end_seconds,
        resolution=resolution,
        name=name,
        style={"prompt": prompt},
        wait_for_completion=True,
        download_outputs=True,
        download_directory=output_dir,
    )

    status = getattr(result, "status", None)
    if status != "complete":
        error = getattr(result, "error_message", None) or str(status)
        raise MagicHourError(f"Magic Hour generation failed: {error}")

    paths = getattr(result, "downloaded_paths", None) or []
    if not paths:
        raise MagicHourError("Magic Hour completed but returned no output files")

    output = paths[0]
    logger.info("Magic Hour: job complete, credits=%s, video=%s", getattr(result, "credits_charged", "?"), output)
    return output
