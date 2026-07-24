#!/usr/bin/env python3
"""
gen_icons.py
------------
產生「成功大學榕園」PWA 所需的所有圖示 (icons)。

設計概念：
- 背景採用品牌綠色漸層 (brand-700 -> brand-500)，呼應網站的 brand 色票
- 主圖為簡化的榕樹造型（樹冠 + 樹幹 + 氣根），代表榕園意象
- 產出標準 PWA 尺寸，以及 Apple Touch Icon 與傳統 favicon

使用方式：
    pip install Pillow --break-system-packages
    python3 gen_icons.py

執行後，圖片會輸出到 ./icons 資料夾。
"""

import os
import math
from PIL import Image, ImageDraw

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")

# 與 index.html 中 tailwind.config 的 brand 色票對齊
BRAND_900 = (26, 68, 49)      # #1a4431
BRAND_800 = (31, 83, 58)      # #1f533a
BRAND_700 = (36, 105, 72)     # #246948
BRAND_600 = (43, 131, 88)     # #2b8358
BRAND_500 = (59, 164, 112)    # #3ba470
BRAND_400 = (95, 193, 142)    # #5fc18e
BRAND_300 = (148, 219, 179)   # #94dbb3
WHITE = (255, 255, 255)

# 標準 PWA 圖示尺寸 (manifest.json 會引用這些)
PWA_SIZES = [72, 96, 128, 144, 152, 192, 384, 512]
# 額外的裝置圖示
APPLE_TOUCH_SIZE = 180
FAVICON_SIZES = [16, 32]


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def draw_vertical_gradient(draw, size, top_color, bottom_color):
    for y in range(size):
        t = y / max(size - 1, 1)
        color = lerp(top_color, bottom_color, t)
        draw.line([(0, y), (size, y)], fill=color)


def draw_banyan_tree(draw, size):
    """在畫布中央畫一棵簡化的榕樹 (樹冠 + 樹幹 + 氣根)"""
    cx, cy = size / 2, size / 2

    # ---- 樹冠：以多個重疊圓形組成蓬鬆樹冠 ----
    canopy_cy = size * 0.40
    canopy_r = size * 0.30
    blob_offsets = [
        (0, 0, 1.0),
        (-0.62, 0.12, 0.72),
        (0.62, 0.12, 0.72),
        (-0.30, -0.42, 0.62),
        (0.30, -0.42, 0.62),
        (0, 0.42, 0.68),
    ]
    for dx, dy, scale in blob_offsets:
        r = canopy_r * scale
        bx = cx + dx * canopy_r
        by = canopy_cy + dy * canopy_r
        draw.ellipse(
            [bx - r, by - r, bx + r, by + r],
            fill=BRAND_300,
        )
    # 內層較深綠色，做出層次感
    for dx, dy, scale in blob_offsets:
        r = canopy_r * scale * 0.72
        bx = cx + dx * canopy_r
        by = canopy_cy + dy * canopy_r
        draw.ellipse(
            [bx - r, by - r, bx + r, by + r],
            fill=BRAND_400,
        )

    # ---- 樹幹 ----
    trunk_top = canopy_cy + canopy_r * 0.55
    trunk_bottom = size * 0.86
    trunk_width_top = size * 0.075
    trunk_width_bottom = size * 0.16
    draw.polygon(
        [
            (cx - trunk_width_top, trunk_top),
            (cx + trunk_width_top, trunk_top),
            (cx + trunk_width_bottom, trunk_bottom),
            (cx - trunk_width_bottom, trunk_bottom),
        ],
        fill=BRAND_900,
    )

    # ---- 氣根 (榕樹特色) ----
    root_count = 3
    for i in range(root_count):
        t = (i + 1) / (root_count + 1)
        rx = cx - trunk_width_top * 0.9 + (2 * trunk_width_top * 0.9) * t
        top_y = canopy_cy + canopy_r * 0.35
        bottom_y = trunk_bottom - size * 0.02
        width = size * 0.018
        wobble = math.sin(t * math.pi) * size * 0.02
        draw.line(
            [(rx, top_y), (rx + wobble, bottom_y)],
            fill=BRAND_900,
            width=max(int(width), 1),
        )

    # ---- 地面草地弧線 ----
    ground_y = trunk_bottom
    draw.rectangle([0, ground_y, size, size], fill=BRAND_700)
    draw.ellipse(
        [-size * 0.1, ground_y - size * 0.05, size * 1.1, ground_y + size * 0.12],
        fill=BRAND_700,
    )


def make_icon(size, maskable=False):
    img = Image.new("RGB", (size, size), BRAND_500)
    draw = ImageDraw.Draw(img)
    draw_vertical_gradient(draw, size, BRAND_600, BRAND_800)

    if maskable:
        # maskable icon 需保留安全區（約 40% padding），避免被系統裁切
        content = Image.new("RGB", (int(size * 0.7), int(size * 0.7)), BRAND_500)
        c_draw = ImageDraw.Draw(content)
        draw_vertical_gradient(c_draw, content.width, BRAND_600, BRAND_800)
        draw_banyan_tree(c_draw, content.width)
        offset = ((size - content.width) // 2, (size - content.height) // 2)
        img.paste(content, offset)
    else:
        draw_banyan_tree(draw, size)
        # 圓角處理，讓一般 icon 更精緻
        img = add_rounded_corners(img, radius_ratio=0.18)

    return img


def add_rounded_corners(img, radius_ratio=0.18):
    size = img.size[0]
    radius = int(size * radius_ratio)
    mask = Image.new("L", img.size, 0)
    mdraw = ImageDraw.Draw(mask)
    mdraw.rounded_rectangle([0, 0, size, size], radius=radius, fill=255)
    rounded = Image.new("RGBA", img.size, (0, 0, 0, 0))
    rounded.paste(img, (0, 0), mask=mask)
    return rounded


def make_favicon(size):
    img = Image.new("RGB", (size, size), BRAND_500)
    draw = ImageDraw.Draw(img)
    draw_vertical_gradient(draw, size, BRAND_500, BRAND_800)
    draw_banyan_tree(draw, size)
    return img


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for size in PWA_SIZES:
        icon = make_icon(size, maskable=False)
        path = os.path.join(OUTPUT_DIR, f"icon-{size}x{size}.png")
        icon.save(path, "PNG")
        print(f"✓ 產生 {path}")

    # maskable 版本 (Android 自適應圖示需要)，使用 512 尺寸即可涵蓋大部分需求
    maskable_512 = make_icon(512, maskable=True)
    maskable_path = os.path.join(OUTPUT_DIR, "icon-maskable-512x512.png")
    maskable_512.save(maskable_path, "PNG")
    print(f"✓ 產生 {maskable_path}")

    # Apple touch icon
    apple_icon = make_icon(APPLE_TOUCH_SIZE, maskable=False).convert("RGB")
    apple_path = os.path.join(OUTPUT_DIR, "apple-touch-icon.png")
    apple_icon.save(apple_path, "PNG")
    print(f"✓ 產生 {apple_path}")

    # Favicon
    for size in FAVICON_SIZES:
        favicon = make_favicon(size)
        path = os.path.join(OUTPUT_DIR, f"favicon-{size}x{size}.png")
        favicon.save(path, "PNG")
        print(f"✓ 產生 {path}")

    # .ico (結合 16/32 尺寸)
    ico_path = os.path.join(OUTPUT_DIR, "favicon.ico")
    make_favicon(32).save(
        ico_path,
        format="ICO",
        sizes=[(16, 16), (32, 32)],
    )
    print(f"✓ 產生 {ico_path}")

    print("\n全部圖示已產生完成！請確認 manifest.json 中的路徑與這裡的檔名一致。")


if __name__ == "__main__":
    main()
