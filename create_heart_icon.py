import os
import sys
import math
from PIL import Image, ImageDraw

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def generate_heart_image(size: int) -> Image.Image:
    """Tạo hình ảnh trái tim chất lượng cao theo kích thước chỉ định."""
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Nền tròn viền hồng mềm mại
    padding = size * 0.03
    draw.ellipse([padding, padding, size - padding, size - padding], fill=(255, 230, 238, 240))

    # Tọa độ trái tim bằng phương trình tham số
    heart_points = []
    cx = size / 2.0
    cy = size * 0.54
    scale = size / 37.6
    for t in range(0, 360, 2):
        rad = math.radians(t)
        x = 16 * (math.sin(rad) ** 3)
        y = -(13 * math.cos(rad) - 5 * math.cos(2 * rad) - 2 * math.cos(3 * rad) - math.cos(4 * rad))
        px = cx + x * scale
        py = cy + y * scale
        heart_points.append((px, py))

    draw.polygon(heart_points, fill=(255, 75, 110, 255))

    # Điểm sáng highlight trên góc trái tim
    hl_x1 = size * 0.28
    hl_y1 = size * 0.30
    hl_x2 = size * 0.42
    hl_y2 = size * 0.42
    draw.ellipse([hl_x1, hl_y1, hl_x2, hl_y2], fill=(255, 170, 195, 220))

    return image


def create_all_icons(ico_output="heart.ico", static_dir="static"):
    """Tạo cả heart.ico cho Windows và các icon PNG cho Mobile PWA."""
    os.makedirs(static_dir, exist_ok=True)

    # 1. Tạo ICO đa kích thước
    img_256 = generate_heart_image(256)
    img_256.save(ico_output, format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
    print(f"✅ Đã tạo icon Windows: {ico_output}")

    # 2. Tạo PNG cho PWA Mobile
    pwa_sizes = {
        "icon-192.png": 192,
        "icon-512.png": 512,
        "apple-touch-icon.png": 180
    }
    for filename, size in pwa_sizes.items():
        out_path = os.path.join(static_dir, filename)
        img = generate_heart_image(size)
        img.save(out_path, format="PNG")
        print(f"✅ Đã tạo PWA Icon: {out_path} ({size}x{size})")


if __name__ == "__main__":
    create_all_icons()
