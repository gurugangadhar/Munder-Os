"""
Munder Difflin — Authentic Scranton Office Map Renderer
Composites the authentic Tiled map layers (floor, walls, furniture-below, furniture-above)
from office.tmj and LimeZu pixel-art tilesets into a crisp, pixel-perfect PNG.
"""

import json
import os
from PIL import Image

FLIPPED_H_FLAG = 0x80000000
FLIPPED_V_FLAG = 0x40000000
FLIPPED_D_FLAG = 0x20000000
TILE_ID_MASK = 0x1FFFFFFF

ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dashboard", "static", "assets"))
TMJ_PATH = os.path.join(ASSETS_DIR, "office.tmj")
OUTPUT_PATH = os.path.join(ASSETS_DIR, "scranton_office_floor.png")


def render_map():
    with open(TMJ_PATH, "r", encoding="utf-8") as f:
        tmj = json.load(f)

    map_w = tmj["width"]  # 34
    map_h = tmj["height"]  # 22
    tile_size = tmj["tilewidth"]  # 16

    img_w = map_w * tile_size  # 544
    img_h = map_h * tile_size  # 352

    canvas = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))

    # Load tilesets
    tileset_images = {
        1: Image.open(os.path.join(ASSETS_DIR, "office-tileset.png")).convert("RGBA"),
        513: Image.open(os.path.join(ASSETS_DIR, "a5-office-floors-walls.png")).convert("RGBA"),
        1025: Image.open(os.path.join(ASSETS_DIR, "interiors.png")).convert("RGBA"),
    }

    tileset_meta = {
        1: {"cols": 16, "tw": 16, "th": 16},
        513: {"cols": 16, "tw": 16, "th": 16},
        1025: {"cols": 16, "tw": 16, "th": 16},
    }

    def resolve_tileset(tile_id):
        if tile_id >= 1025:
            return 1025
        elif tile_id >= 513:
            return 513
        elif tile_id >= 1:
            return 1
        return None

    layers_to_render = ["floor", "walls", "furniture-below", "furniture-above"]

    for layer_name in layers_to_render:
        layer = next((l for l in tmj["layers"] if l["name"] == layer_name and l["type"] == "tilelayer"), None)
        if not layer or not layer.get("data"):
            continue

        print(f"Rendering layer: {layer_name}...")
        for y in range(map_h):
            for x in range(map_w):
                raw = layer["data"][y * map_w + x]
                if raw == 0:
                    continue

                flip_h = bool(raw & FLIPPED_H_FLAG)
                flip_v = bool(raw & FLIPPED_V_FLAG)
                flip_d = bool(raw & FLIPPED_D_FLAG)
                tile_id = raw & TILE_ID_MASK

                ts_firstgid = resolve_tileset(tile_id)
                if not ts_firstgid:
                    continue

                ts_img = tileset_images[ts_firstgid]
                meta = tileset_meta[ts_firstgid]
                local_id = tile_id - ts_firstgid
                cols = meta["cols"]
                tw = meta["tw"]
                th = meta["th"]

                src_x = (local_id % cols) * tw
                src_y = (local_id // cols) * th

                # Crop tile from tileset
                tile_crop = ts_img.crop((src_x, src_y, src_x + tw, src_y + th))

                # Handle flips
                if flip_d:
                    # Diagonal flip is transpose (swap x and y)
                    tile_crop = tile_crop.transpose(Image.Transpose.TRANSPOSE)
                if flip_h:
                    tile_crop = tile_crop.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                if flip_v:
                    tile_crop = tile_crop.transpose(Image.Transpose.FLIP_TOP_BOTTOM)

                # Composite onto canvas
                dest_x = x * tile_size
                dest_y = y * tile_size
                canvas.alpha_composite(tile_crop, (dest_x, dest_y))

    # Save at 1x native and 2x scaled for high-res crispness
    canvas.save(OUTPUT_PATH, "PNG")
    print(f"[OK] Rendered native map to: {OUTPUT_PATH} ({img_w}x{img_h})")

    # 2x scaled with nearest neighbor for pixel art sharpness
    scaled_2x = canvas.resize((img_w * 2, img_h * 2), Image.Resampling.NEAREST)
    scaled_2x_path = os.path.join(ASSETS_DIR, "scranton_office_floor_2x.png")
    scaled_2x.save(scaled_2x_path, "PNG")
    print(f"[OK] Rendered 2x crisp map to: {scaled_2x_path} ({img_w*2}x{img_h*2})")


if __name__ == "__main__":
    render_map()
