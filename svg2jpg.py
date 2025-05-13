import os
import argparse
from cairosvg import svg2png
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

def svg_to_jpg(svg_path, jpg_path, width):
    with open(svg_path, 'r') as f:
        svg_content = f.read()

    png_data = svg2png(bytestring=svg_content, output_width=width)

    with open('temp.png', 'wb') as temp_file:
        temp_file.write(png_data)

    img = Image.open('temp.png').convert('RGB')
    img.save(jpg_path, 'JPEG', quality=95)
    os.remove('temp.png')

def main():
    parser = argparse.ArgumentParser(description='批量将SVG转换为JPG')
    parser.add_argument('--width', type=int, default=20000, help='图片宽度，默认20000px')
    args = parser.parse_args()

    input_dir = 'uploads/svgs'
    output_dir = 'uploads/jpg'
    os.makedirs(output_dir, exist_ok=True)

    for filename in os.listdir(input_dir):
        if filename.lower().endswith('.svg'):
            svg_path = os.path.join(input_dir, filename)
            jpg_path = os.path.join(output_dir, filename[:-4] + '.jpg')
            svg_to_jpg(svg_path, jpg_path, args.width)
            print(f'✅ 转换完成: {filename} → {jpg_path} (宽度: {args.width}px)')

if __name__ == '__main__':
    main()