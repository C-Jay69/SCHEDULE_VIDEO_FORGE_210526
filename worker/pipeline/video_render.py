import contextlib
import logging
import os
import shutil
import subprocess
import tempfile
import textwrap

from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

# 9:16 vertical short-form
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
FPS = 30

BACKGROUND_COLORS = [
    ("#0f0c29", "#302b63"),  # Deep purple
    ("#134e5e", "#71b280"),  # Teal green
    ("#1a1a2e", "#16213e"),  # Dark blue
    ("#0f2027", "#2c5364"),  # Dark cyan
    ("#16213e", "#0f3460"),  # Navy blue
]

WATERMARK_TEXT = "VideoForge"


def render_video(
    audio_path: str,
    srt_path: str,
    output_path: str,
    topic: str,
    add_watermark: bool = True,
    bg_color_index: int = 0,
) -> str:
    """
    Assemble final video with FFmpeg.
    - Gradient background
    - Burned-in subtitles from SRT
    - Audio track
    - Optional watermark
    Returns output_path.
    """
    tmpdir = tempfile.mkdtemp()

    try:
        # Get audio duration
        from .tts import get_audio_duration

        duration = get_audio_duration(audio_path)
        logger.info(f"Audio duration: {duration}s")

        # Create background image
        bg_path = os.path.join(tmpdir, "background.png")
        _create_gradient_background(bg_path, bg_color_index, topic)

        # Build FFmpeg filter chain
        filters = _build_filter_chain(
            srt_path=srt_path,
            add_watermark=add_watermark,
            duration=duration,
        )

        # Assemble with FFmpeg
        cmd = [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-framerate",
            str(FPS),
            "-i",
            bg_path,
            "-i",
            audio_path,
            "-vf",
            filters,
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "23",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-t",
            str(duration),
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            output_path,
        ]

        logger.info(f"Running FFmpeg: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

        if result.returncode != 0:
            logger.error(f"FFmpeg error:\n{result.stderr}")
            raise RuntimeError(f"FFmpeg failed: {result.stderr[-500:]}")

        logger.info(f"Video rendered: {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"Video render failed: {e}")
        raise
    finally:
        # Cleanup temp files
        with contextlib.suppress(Exception):
            shutil.rmtree(tmpdir)


def _create_gradient_background(output_path: str, color_index: int = 0, title: str = ""):
    """Create a gradient background PNG with topic title."""
    idx = color_index % len(BACKGROUND_COLORS)
    color1_hex, color2_hex = BACKGROUND_COLORS[idx]

    c1 = _hex_to_rgb(color1_hex)
    c2 = _hex_to_rgb(color2_hex)

    img = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), c1)
    draw = ImageDraw.Draw(img)

    # Draw vertical gradient
    for y in range(VIDEO_HEIGHT):
        ratio = y / VIDEO_HEIGHT
        r = int(c1[0] * (1 - ratio) + c2[0] * ratio)
        g = int(c1[1] * (1 - ratio) + c2[1] * ratio)
        b = int(c1[2] * (1 - ratio) + c2[2] * ratio)
        draw.line([(0, y), (VIDEO_WIDTH, y)], fill=(r, g, b))

    # Add title text at top
    if title:
        try:
            font_size = 60
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        except OSError:
            font = ImageFont.load_default()

        # Wrap title
        wrapped = textwrap.fill(title[:80], width=18)
        lines = wrapped.split("\n")

        y_start = VIDEO_HEIGHT // 6
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (VIDEO_WIDTH - text_width) // 2
            # Shadow
            draw.text((x + 3, y_start + 3), line, fill=(0, 0, 0, 128), font=font)
            draw.text((x, y_start), line, fill=(255, 255, 255), font=font)
            y_start += 80

    img.save(output_path, "PNG")


def _build_filter_chain(srt_path: str, add_watermark: bool, duration: float) -> str:
    """Build FFmpeg -vf filter string."""
    filters = [f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease"]
    filters.append(f"pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2")

    # Subtitles
    if os.path.exists(srt_path) and os.path.getsize(srt_path) > 0:
        # Escape path for FFmpeg filter
        srt_escaped = srt_path.replace("\\", "/").replace(":", "\\:")
        subtitle_filter = (
            f"subtitles='{srt_escaped}'"
            f":force_style='FontSize=28,FontName=DejaVu Sans,"
            f"PrimaryColour=&HFFFFFF,OutlineColour=&H000000,"
            f"Outline=2,Shadow=1,Alignment=2,MarginV=80'"
        )
        filters.append(subtitle_filter)

    # Watermark
    if add_watermark:
        filters.append(f"drawtext=text='{WATERMARK_TEXT}':fontcolor=white@0.5:fontsize=32:x=w-tw-30:y=30")

    return ",".join(filters)


def _hex_to_rgb(hex_color: str) -> tuple:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
