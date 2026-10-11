"""
Munder Difflin — Ryan's Visual Design Agent
Renders high-contrast, modern 1080×1920 vertical slides and infographic cards
using Pillow with bold Windows TrueType typography and dark mode styling.
"""

import os
from typing import List
from PIL import Image, ImageDraw, ImageFont
from core.media.scriptwriter import VideoScene


class VisualAgent:
    """Ryan Howard — Visual Layout & Card Generator Agent."""

    WIDTH = 1080
    HEIGHT = 1920

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        # Load crisp Windows TrueType fonts with fallbacks
        try:
            self.font_header = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 28)
            self.font_badge = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 30)
            self.font_title = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 62)
            self.font_subtitle = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 38)
            self.font_code = ImageFont.truetype("C:/Windows/Fonts/consolab.ttf", 36)
            self.font_footer = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 28)
        except Exception:
            self.font_header = None
            self.font_badge = None
            self.font_title = None
            self.font_subtitle = None
            self.font_code = None
            self.font_footer = None

    def render_scene_card(self, scene: VideoScene) -> str:
        """Renders a single 1080x1920 vertical slide with crisp, bold typography."""
        img = Image.new("RGBA", (self.WIDTH, self.HEIGHT), (15, 23, 42, 255))  # Deep navy background
        draw = ImageDraw.Draw(img)

        # 1. Background Grid Pattern
        grid_color = (28, 38, 58, 255)
        for x in range(0, self.WIDTH, 90):
            draw.line([(x, 0), (x, self.HEIGHT)], fill=grid_color, width=1)
        for y in range(0, self.HEIGHT, 90):
            draw.line([(0, y), (self.WIDTH, y)], fill=grid_color, width=1)

        card_margin = 60
        card_w = self.WIDTH - 2 * card_margin

        # 2. Outer Border Frame
        draw.rectangle([card_margin, 160, self.WIDTH - card_margin, self.HEIGHT - 220], outline=scene.accent_color, width=5)

        # 3. Top Header Bar
        draw.rectangle([card_margin, 160, self.WIDTH - card_margin, 250], fill=(22, 33, 56, 255))
        draw.text((card_margin + 35, 192), "MUNDER DIFFLIN  //  AUTONOMOUS TECH MEDIA", fill=(148, 163, 184), font=self.font_header)

        # 4. Scene Number Pill Badge
        badge_rect = [card_margin + 35, 310, card_margin + 280, 375]
        draw.rectangle(badge_rect, fill=scene.accent_color)
        draw.text((card_margin + 55, 328), f"SCENE 0{scene.scene_index} / 05", fill=(15, 23, 42), font=self.font_badge)

        # 5. Bold Headline & Underline
        draw.text((card_margin + 35, 420), scene.headline, fill=(255, 255, 255), font=self.font_title)
        draw.line([(card_margin + 35, 505), (card_margin + 500, 505)], fill=scene.accent_color, width=4)

        # 6. Subtitle / Tagline
        draw.text((card_margin + 35, 530), scene.subtext, fill=(203, 213, 225), font=self.font_subtitle)

        # 7. Sleek Code Terminal Container
        term_y = 660
        term_h = 760
        term_rect = [card_margin + 35, term_y, self.WIDTH - card_margin - 35, term_y + term_h]
        draw.rectangle(term_rect, fill=(10, 15, 29, 255), outline=(51, 65, 85), width=2)

        # Terminal Header with Red/Yellow/Green window dots
        draw.rectangle([card_margin + 35, term_y, self.WIDTH - card_margin - 35, term_y + 65], fill=(22, 30, 49, 255))
        draw.ellipse([card_margin + 60, term_y + 24, card_margin + 78, term_y + 42], fill=(239, 68, 68))
        draw.ellipse([card_margin + 90, term_y + 24, card_margin + 108, term_y + 42], fill=(245, 158, 11))
        draw.ellipse([card_margin + 120, term_y + 24, card_margin + 138, term_y + 42], fill=(34, 197, 94))
        draw.text((card_margin + 160, term_y + 20), "local_agent_terminal ~ bash", fill=(100, 116, 139), font=self.font_header)

        # Spoken text formatted into terminal lines
        words = scene.spoken_text.split()
        lines = []
        cur = []
        for w in words:
            cur.append(w)
            if len(" ".join(cur)) > 30:
                lines.append(" ".join(cur))
                cur = []
        if cur:
            lines.append(" ".join(cur))

        y_offset = term_y + 110
        for i, line in enumerate(lines[:8]):
            prefix = "$ " if i == 0 else "  "
            color = (56, 189, 248) if i == 0 else (241, 245, 249)
            draw.text((card_margin + 70, y_offset), f"{prefix}{line}", fill=color, font=self.font_code)
            y_offset += 65

        # 8. Bottom Footer Status Bar
        draw.rectangle([card_margin, self.HEIGHT - 320, self.WIDTH - card_margin, self.HEIGHT - 220], fill=(22, 33, 56, 255))
        draw.text((card_margin + 35, self.HEIGHT - 280), "⚡ Autonomous AI Pipeline | Verified Rs. 0.00 Cost", fill=(52, 211, 153), font=self.font_footer)

        output_path = os.path.join(self.output_dir, f"scene_{scene.scene_index}.png")
        img.save(output_path, "PNG")
        return output_path

    def render_all_cards(self, scenes: List[VideoScene]) -> List[str]:
        """Renders cards for all scenes in the script."""
        return [self.render_scene_card(s) for s in scenes]
