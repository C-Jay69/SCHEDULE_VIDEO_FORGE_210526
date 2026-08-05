import logging
import os
import textwrap

from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

THUMBNAIL_WIDTH = 1280
THUMBNAIL_HEIGHT = 720

BACKGROUND_COLORS = [
    ("#0f0c29", "#302b63"),  # Deep purple
    ("#134e5e", "#71b280"),  # Teal green
    ("#1a1a2e", "#16213e"),  # Dark blue
    ("#0f2027", "#2c5364"),  # Dark cyan
    ("#16213e", "#0f3460"),  # Navy blue
]

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]


def _load_font(size: int):
    for candidate in FONT_CANDIDATES:
        if os.path.exists(candidate):
            try:
                return ImageFont.truetype(candidate, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _hex_to_rgb(hex_color: str) -> tuple:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def _gradient(width: int, height: int, top: str, bottom: str) -> Image.Image:
    image = Image.new("RGB", (width, height))
    top_rgb = _hex_to_rgb(top)
    bottom_rgb = _hex_to_rgb(bottom)
    draw = ImageDraw.Draw(image)
    for y in range(height):
        t = y / max(height - 1, 1)
        r = int(top_rgb[0] + (bottom_rgb[0] - top_rgb[0]) * t)
        g = int(top_rgb[1] + (bottom_rgb[1] - top_rgb[1]) * t)
        b = int(top_rgb[2] + (bottom_rgb[2] - top_rgb[2]) * t)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    return image


class ThumbnailProvider:
    """Generates a branded YouTube-style thumbnail from a template + text overlay."""

    def generate_thumbnail(
        self,
        title: str,
        output_path: str,
        color_index: int = 0,
        channel_label: str = "VideoForge",
        video_path: str | None = None,
    ) -> str:
        """
        Render a thumbnail using the built-in gradient template with a text overlay.

        - video_path: if provided, a frame is extracted from the video and used as the
          background instead of the gradient template.
        - channel_label: small text badge rendered at the top.
        Returns output_path.
        """
        if video_path and os.path.exists(video_path):
            try:
                image = self._frame_from_video(video_path)
                image = image.resize((THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), Image.LANCZOS)
            except Exception as e:
                logger.warning(f"Could not extract video frame for thumbnail: {e}")
                image = self._template_background(color_index)
        else:
            image = self._template_background(color_index)

        draw = ImageDraw.Draw(image, "RGBA")
        _, h = image.size

        # Channel badge
        badge_font = _load_font(28)
        badge_padding = 12
        badge_text = channel_label.upper()
        bbox = draw.textbbox((0, 0), badge_text, font=badge_font)
        badge_w = bbox[2] - bbox[0] + badge_padding * 2
        badge_h = bbox[3] - bbox[1] + badge_padding * 2
        draw.rounded_rectangle(
            [20, 20, 20 + badge_w, 20 + badge_h],
            radius=8,
            fill=(255, 255, 255, 220),
        )
        draw.text(
            (20 + badge_padding, 20 + badge_padding - bbox[1]),
            badge_text,
            font=badge_font,
            fill=(20, 20, 20, 255),
        )

        # Title text with shadow
        title_font = _load_font(72)
        title_lines = textwrap.wrap(title, width=24)
        title_lines = title_lines[:3]
        line_height = title_font.size + 12
        start_y = h - 120 - len(title_lines) * line_height

        for i, line in enumerate(title_lines):
            line_y = start_y + i * line_height
            shadow_offset = 4
            draw.text(
                (30 + shadow_offset, line_y + shadow_offset),
                line,
                font=title_font,
                fill=(0, 0, 0, 200),
            )
            draw.text((30, line_y), line, font=title_font, fill=(255, 255, 255, 255))

        image.save(output_path, format="JPEG", quality=88)
        logger.info(f"Thumbnail generated: {output_path}")
        return output_path

    def _template_background(self, color_index: int) -> Image.Image:
        colors = BACKGROUND_COLORS[color_index % len(BACKGROUND_COLORS)]
        return _gradient(THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT, colors[0], colors[1])

    def _frame_from_video(self, video_path: str) -> Image.Image:
        import subprocess
        import tempfile

        frame_path = os.path.join(tempfile.mkdtemp(), "frame.png")
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            video_path,
            "-ss",
            "1",
            "-vframes",
            "1",
            "-f",
            "image2",
            frame_path,
        ]
        subprocess.run(cmd, capture_output=True, check=True, timeout=60)
        return Image.open(frame_path).convert("RGB")


# Singleton for use across the worker
thumbnail_provider = ThumbnailProvider()
