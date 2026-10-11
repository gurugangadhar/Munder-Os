"""
Slice cast.png into individual character sprites and avatar portraits.
cast.png is 90x480: 15 characters (height 32px), 5 frames per character (width 18px).
"""

import os
from PIL import Image

ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dashboard", "static", "assets"))
CAST_PATH = os.path.join(ASSETS_DIR, "cast.png")
OUTPUT_DIR = os.path.join(ASSETS_DIR, "characters")
os.makedirs(OUTPUT_DIR, exist_ok=True)

CHARACTERS = [
    "michael", "jim", "pam", "dwight", "kevin",
    "angela", "oscar", "stanley", "phyllis", "andy",
    "kelly", "ryan", "toby", "creed", "meredith"
]

FRAME_W = 18
FRAME_H = 32

cast_img = Image.open(CAST_PATH).convert("RGBA")

for row, name in enumerate(CHARACTERS):
    y = row * FRAME_H

    # Frame 0: idle stand (18x32)
    idle_crop = cast_img.crop((0, y, FRAME_W, y + FRAME_H))
    idle_path = os.path.join(OUTPUT_DIR, f"{name}.png")
    idle_crop.save(idle_path)

    # 4x scaled for crisp high-res display
    idle_4x = idle_crop.resize((FRAME_W * 4, FRAME_H * 4), Image.Resampling.NEAREST)
    idle_4x.save(os.path.join(OUTPUT_DIR, f"{name}_4x.png"))

    # Frame 4: portrait avatar bust (18x28 or 18x32)
    avatar_crop = cast_img.crop((FRAME_W * 4, y, FRAME_W * 5, y + FRAME_H))
    avatar_path = os.path.join(OUTPUT_DIR, f"avatar_{name}.png")
    avatar_crop.save(avatar_path)

    avatar_4x = avatar_crop.resize((FRAME_W * 4, FRAME_H * 4), Image.Resampling.NEAREST)
    avatar_4x.save(os.path.join(OUTPUT_DIR, f"avatar_{name}_4x.png"))

print(f"[OK] Successfully sliced 15 characters into: {OUTPUT_DIR}")
