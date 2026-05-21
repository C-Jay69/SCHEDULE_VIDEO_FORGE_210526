import os
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)

WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base")

# Cache model in memory across tasks
_whisper_model = None


def get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel
        logger.info(f"Loading Whisper model: {WHISPER_MODEL_SIZE}")
        _whisper_model = WhisperModel(
            WHISPER_MODEL_SIZE,
            device="cpu",
            compute_type="int8",
        )
    return _whisper_model


def generate_subtitles(audio_path: str, output_srt_path: str) -> str:
    """
    Transcribe audio and generate SRT subtitle file.
    Returns path to .srt file.
    """
    try:
        model = get_whisper_model()
        segments, info = model.transcribe(
            audio_path,
            beam_size=3,
            language="en",
            word_timestamps=True,
        )

        srt_content = _segments_to_srt(list(segments))

        with open(output_srt_path, "w", encoding="utf-8") as f:
            f.write(srt_content)

        logger.info(f"Subtitles generated: {output_srt_path}")
        return output_srt_path

    except ImportError:
        logger.warning("faster-whisper not installed, skipping subtitles")
        # Create empty SRT
        with open(output_srt_path, "w") as f:
            f.write("")
        return output_srt_path
    except Exception as e:
        logger.error(f"Subtitle generation failed: {e}")
        # Non-fatal — return empty SRT
        with open(output_srt_path, "w") as f:
            f.write("")
        return output_srt_path


def _segments_to_srt(segments) -> str:
    """Convert whisper segments to SRT format."""
    srt_lines = []
    idx = 1

    for segment in segments:
        start = _format_timestamp(segment.start)
        end = _format_timestamp(segment.end)
        text = segment.text.strip()

        if text:
            srt_lines.append(f"{idx}")
            srt_lines.append(f"{start} --> {end}")
            srt_lines.append(text)
            srt_lines.append("")
            idx += 1

    return "\n".join(srt_lines)


def _format_timestamp(seconds: float) -> str:
    """Format seconds to SRT timestamp HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
