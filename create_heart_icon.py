import sys
import math
from PIL import Image, ImageDraw

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def create_heart_icon(output_path="heart.ico"):
    """Tạo icon hình trái tim hồng ngọt ngào chất lượng cao cho ứng dụng."""
    size = (256, 256)
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # Vẽ nền tròn gradient hoặc bóng mờ nhẹ
    draw.ellipse([8, 8, 248, 248], fill=(255, 230, 238, 240))
    
    # Tọa độ trái tim bằng phương trình tham số
    heart_points = []
    cx, cy = 128, 138
    scale = 6.8
    for t in range(0, 360, 2):
        rad = math.radians(t)
        # x = 16 sin^3(t)
        x = 16 * (math.sin(rad) ** 3)
        # y = -(13 cos(t) - 5 cos(2t) - 2 cos(3t) - cos(4t))
        y = -(13 * math.cos(rad) - 5 * math.cos(2*rad) - 2 * math.cos(3*rad) - math.cos(4*rad))
        px = cx + x * scale
        py = cy + y * scale
        heart_points.append((px, py))
        
    draw.polygon(heart_points, fill=(255, 75, 110, 255))
    
    # Thêm điểm sáng highlight trên góc trái tim
    draw.ellipse([70, 75, 105, 105], fill=(255, 160, 185, 200))
    
    # Lưu dưới dạng ICO hỗ trợ nhiều kích thước
    image.save(output_path, format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
    print(f"Đã tạo icon thành công tại: {output_path}")

if __name__ == "__main__":
    create_heart_icon()
