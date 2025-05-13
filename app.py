from flask import Flask, request, jsonify, send_from_directory, render_template
from werkzeug.utils import secure_filename
import uuid
from PIL import Image
import cairosvg
import os
import imageio
# import pythoncom
# import win32com.client

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'svg'}
DWG_FOLDER = os.path.join(UPLOAD_FOLDER, 'dwg')
PDF_FOLDER = os.path.join(OUTPUT_FOLDER, 'pdf')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# 创建必要目录
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DWG_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(PDF_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def convert_image(input_path, output_path, format):
    with Image.open(input_path) as img:
        if format == 'jpg':
            img = img.convert("RGB")  # JPG 不支持透明背景
        img.save(output_path, format=format.upper())

def convert_svg(input_path, output_path, format):
    # 先将 SVG 转为 PNG（cairosvg 不支持直接转 JPG）
    temp_png_path = output_path.rsplit('.', 1)[0] + '.png'
    cairosvg.svg2png(url=input_path, write_to=temp_png_path)
    with Image.open(temp_png_path) as img:
        if format == 'jpg':
            img = img.convert("RGB")
        img.save(output_path, format=format.upper())
    os.remove(temp_png_path)

# ✅ DWG 转 PDF（Windows Only）
# def convert_dwg_to_pdf(dwg_path, pdf_output_path):
#     import pythoncom
#     import win32com.client

#     pythoncom.CoInitialize()
#     acad = win32com.client.Dispatch("AutoCAD.Application")
#     acad.Visible = False
#     doc = acad.Documents.Open(dwg_path)
#     doc.SetVariable("BACKGROUNDPLOT", 0)

#     dsd_path = os.path.splitext(dwg_path)[0] + ".dsd"
#     pdf_output_dir = os.path.dirname(pdf_output_path)

#     dsd_content = f"""[DWF6Version]
# Ver=1
# [DWF6MinorVersion]
# MinorVer=1
# [Sheet1]
# DWG={dwg_path}
# Layout=*
# Setup=
# OriginalSheetPath={dwg_path}
# Has PlotStyles=0
# [Target]
# Type=6
# DWF={pdf_output_path}
# OUT={pdf_output_dir}
# PWD=
# [AutoCAD Block Data]
# IncludeLayer=TRUE
# PromptForDwfName=FALSE
# RememberSheetSet=FALSE
# """

#     with open(dsd_path, "w") as f:
#         f.write(dsd_content)

#     acad.Publish.PublishToWeb(dsd_path)
#     doc.Close(False)
#     acad.Quit()
#     pythoncom.CoUninitialize()

# 首页展示
@app.route('/')
def index():
    all_files = []
    for subdir in os.listdir(OUTPUT_FOLDER):
        subdir_path = os.path.join(OUTPUT_FOLDER, subdir)
        if os.path.isdir(subdir_path):
            for file in os.listdir(subdir_path):
                file_path = f"{subdir}/{file}"
                all_files.append(file_path)
    return render_template('index.html', converted_files=all_files)

# 图像和 SVG 转换
@app.route('/convert', methods=['POST'])
def convert():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    convert_type = request.form.get('convert_type')
    if convert_type not in {'webp', 'png', 'jpg'}:
        return jsonify({"error": "无效的转换类型"}), 400

    if file and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = secure_filename(file.filename)
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(input_path)

        base_name = os.path.splitext(filename)[0]
        output_filename = f"{base_name}.{convert_type}"
        output_dir = os.path.join(OUTPUT_FOLDER, convert_type)
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, output_filename)

        try:
            if ext == 'svg':
                convert_svg(input_path, output_path, convert_type)
            else:
                convert_image(input_path, output_path, convert_type)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            if os.path.exists(input_path):
                os.remove(input_path)

        return jsonify({
            "message": "转换成功",
            "output_file": output_filename,
            "download_url": f"/download/{convert_type}/{output_filename}"
        })

    return jsonify({"error": "不支持的文件类型"}), 400



@app.route('/merge_gif', methods=['POST'])
def merge_gif():
    if 'files' not in request.files:
        print("[merge_gif] ❌ 没有收到 'files'")
        return jsonify({'error': '没有上传文件'}), 400

    files = request.files.getlist('files')
    if not files:
        print("[merge_gif] ⚠️ 上传列表为空")
        return jsonify({'error': '未选择任何图片'}), 400

    print(f"[merge_gif] 📥 接收到 {len(files)} 个文件")
    for f in files:
        print(f" - 文件名: {f.filename}")

    duration = request.form.get('duration', 0.5)
    try:
        duration = float(duration)
        print(f"[merge_gif] ⏱️ 每帧间隔时间: {duration} 秒")
    except ValueError:
        print("[merge_gif] ❌ duration 参数无效")
        return jsonify({'error': 'duration 参数无效'}), 400

    images = []
    try:
        for file in files:
            if file.filename == '':
                print("[merge_gif] ⚠️ 空文件名，跳过")
                continue
            if file and allowed_file(file.filename):
                print(f"[merge_gif] ✅ 正在处理文件: {file.filename}")
                img = Image.open(file.stream).convert("RGBA")
                images.append(img)
            else:
                print(f"[merge_gif] ❌ 不支持的文件类型: {file.filename}")
                return jsonify({'error': f'{file.filename} 文件类型不支持'}), 400

        if len(images) < 2:
            print("[merge_gif] ❌ 图片不足两张，无法合成 GIF")
            return jsonify({'error': '至少需要两张图片合成 GIF'}), 400

        gif_dir = os.path.join(OUTPUT_FOLDER, 'gif')
        os.makedirs(gif_dir, exist_ok=True)

        gif_filename = f"combo_{uuid.uuid4().hex}.gif"
        gif_path = os.path.join(gif_dir, gif_filename)

        print(f"[merge_gif] 💾 保存 GIF 路径: {gif_path}")
        imageio.mimsave(gif_path, images, duration=duration)
        print("[merge_gif] ✅ GIF 合成完成")

        return jsonify({
            'message': 'GIF 合成成功',
            'output_file': gif_filename,
            'download_url': f'/download/gif/{gif_filename}'
        })

    except Exception as e:
        print(f"[merge_gif] ❌ 合成过程出错: {str(e)}")
        return jsonify({'error': f'GIF 合成失败: {str(e)}'}), 500
# DWG 转 PDF 路由
@app.route('/dwgtopdf', methods=['POST'])
def dwg_to_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "没有上传 DWG 文件"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "未选择文件"}), 400

    if file and file.filename.lower().endswith('.dwg'):
        filename = secure_filename(file.filename)
        dwg_path = os.path.join(DWG_FOLDER, filename)
        file.save(dwg_path)

        base_name = os.path.splitext(filename)[0]
        output_pdf_path = os.path.join(PDF_FOLDER, f"{base_name}.pdf")

        try:
            convert_dwg_to_pdf(dwg_path, output_pdf_path)
        except Exception as e:
            return jsonify({"error": f"转换失败: {e}"}), 500
        finally:
            if os.path.exists(dwg_path):
                os.remove(dwg_path)

        return jsonify({
            "message": "DWG 转换成功",
            "output_file": f"{base_name}.pdf",
            "download_url": f"/download/pdf/{base_name}.pdf"
        })

    return jsonify({"error": "只支持 DWG 文件"}), 400

@app.route('/download/<format>/<filename>')
def download_file(format, filename):
    folder = os.path.join(OUTPUT_FOLDER, format)
    return send_from_directory(folder, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, port=3010)