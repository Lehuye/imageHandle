import os
import uuid
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QFileDialog,
    QVBoxLayout, QHBoxLayout, QMessageBox, QComboBox
)
from PyQt5.QtCore import Qt
from PIL import Image
import cairosvg
import imageio
import sys

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'svg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def convert_image(input_path, output_path, format):
    with Image.open(input_path) as img:
        if format == 'jpg':
            img = img.convert("RGB")
        img.save(output_path, format=format.upper())

def convert_svg(input_path, output_path, format):
    temp_png_path = output_path.rsplit('.', 1)[0] + '.png'
    cairosvg.svg2png(url=input_path, write_to=temp_png_path)
    with Image.open(temp_png_path) as img:
        if format == 'jpg':
            img = img.convert("RGB")
        img.save(output_path, format=format.upper())
    os.remove(temp_png_path)

class ImageConverter(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("图片/矢量转换工具")
        self.setFixedSize(400, 250)

        layout = QVBoxLayout()

        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("选择转换格式:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["png", "jpg", "webp"])
        format_layout.addWidget(self.format_combo)
        layout.addLayout(format_layout)

        convert_btn = QPushButton("选择文件并转换")
        convert_btn.clicked.connect(self.select_and_convert)
        layout.addWidget(convert_btn)

        duration_layout = QHBoxLayout()
        duration_layout.addWidget(QLabel("GIF 每帧间隔 (秒):"))
        self.duration_combo = QComboBox()
        self.duration_combo.addItems(["0.1", "0.2", "0.5", "1.0"])
        duration_layout.addWidget(self.duration_combo)
        layout.addLayout(duration_layout)

        gif_btn = QPushButton("选择多张图片合成GIF")
        gif_btn.clicked.connect(self.select_and_merge_gif)
        layout.addWidget(gif_btn)

        self.setLayout(layout)

    def select_and_convert(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择多个图片或SVG文件", "", "图像文件 (*.jpg *.jpeg *.png *.svg)"
        )
        if not file_paths:
            return
    
        convert_type = self.format_combo.currentText()
        success_count = 0
        failed_files = []
    
        for file_path in file_paths:
            ext = file_path.rsplit('.', 1)[-1].lower()
            if not allowed_file(file_path):
                failed_files.append(file_path)
                continue
            
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            output_path = os.path.join(os.path.dirname(file_path), f"{base_name}.{convert_type}")
    
            try:
                if ext == 'svg':
                    convert_svg(file_path, output_path, convert_type)
                else:
                    convert_image(file_path, output_path, convert_type)
                success_count += 1
            except Exception as e:
                failed_files.append(file_path)
    
        message = f"成功转换 {success_count} 个文件。"
        if failed_files:
            message += f"\n失败文件:\n" + "\n".join(failed_files)
            QMessageBox.warning(self, "部分失败", message)
        else:
            QMessageBox.information(self, "成功", message)

    def select_and_merge_gif(self):
        file_paths, _ = QFileDialog.getOpenFileNames(self, "选择多张图片合成GIF", "", "图像文件 (*.jpg *.jpeg *.png *.gif)")
        if not file_paths or len(file_paths) < 2:
            QMessageBox.critical(self, "错误", "请至少选择两张图片")
            return

        try:
            images = [Image.open(fp).convert("RGBA") for fp in file_paths]
            duration = float(self.duration_combo.currentText())
            output_path = os.path.join(os.path.dirname(file_paths[0]), f"combo_{uuid.uuid4().hex}.gif")
            imageio.mimsave(output_path, images, duration=duration)
            QMessageBox.information(self, "成功", f"GIF 合成成功！\n输出文件: {output_path}")
        except Exception as e:
            QMessageBox.critical(self, "合成失败", str(e))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ImageConverter()
    window.show()
    sys.exit(app.exec_())
