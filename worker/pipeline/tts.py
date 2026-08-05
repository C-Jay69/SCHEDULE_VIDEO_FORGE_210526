import logging
import os
import subprocess
import tempfile

logger = logging.getLogger(__name__)

PIPER_MODEL_PATH = os.getenv("PIPER_MODEL_PATH", "/app/models/en_US-lessac-medium.onnx")


def generate_voiceover(script_text: str, output_path: str) -> str:
    """
    Generate voiceover audio from script using Piper TTS.
    Returns path to generated .wav file.
    """
    if not os.path.exists(PIPER_MODEL_PATH):
        logger.warning(f"Piper model not found at {PIPER_MODEL_PATH}, using espeak fallback")
        return _espeak_fallback(script_text, output_path)

    try:
        # Write script to temp file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(script_text)
            txt_path = f.name

        # Run Piper TTS
        cmd = [
            "piper",
            "--model",
            PIPER_MODEL_PATH,
            "--output_file",
            output_path,
        ]

        with open(txt_path) as stdin_file:
            result = subprocess.run(
                cmd,
                stdin=stdin_file,
                capture_output=True,
                text=True,
                timeout=300,
            )

        os.unlink(txt_path)

        if result.returncode != 0:
            logger.error(f"Piper TTS error: {result.stderr}")
            raise RuntimeError(f"Piper TTS failed: {result.stderr}")

        logger.info(f"Voiceover generated: {output_path}")
        return output_path

    except FileNotFoundError:
        logger.warning("Piper not installed, using espeak fallback")
        return _espeak_fallback(script_text, output_path)
    except Exception as e:
        logger.error(f"TTS failed: {e}")
        raise


def _espeak_fallback(script_text: str, output_path: str) -> str:
    """Fallback TTS using espeak-ng (lower quality but widely available)."""
    try:
        wav_path = output_path if output_path.endswith(".wav") else output_path + ".wav"
        cmd = [
            "espeak-ng",
            "-v",
            "en-us",
            "-s",
            "150",  # words per minute
            "-w",
            wav_path,
            script_text[:2000],  # Limit length
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            return wav_path
        raise RuntimeError(f"espeak-ng failed: {result.stderr}")
    except FileNotFoundError:
        logger.error("No TTS engine available (piper or espeak-ng)")
        # Create a silent audio file as last resort
        return _create_silent_audio(output_path, duration=60)


def _create_silent_audio(output_path: str, duration: int = 60) -> str:
    """Create silent audio using FFmpeg as absolute fallback."""
    wav_path = output_path if output_path.endswith(".wav") else output_path + ".wav"
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        "anullsrc=r=22050:cl=mono",
        "-t",
        str(duration),
        wav_path,
    ]
    subprocess.run(cmd, capture_output=True, timeout=30)
    return wav_path


def get_audio_duration(audio_path: str) -> float:
    """Get audio duration in seconds using ffprobe."""
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                audio_path,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return float(result.stdout.strip())
    except Exception:
        return 60.0
