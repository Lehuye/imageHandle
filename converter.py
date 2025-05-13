from PIL import Image
import os
import fitz  # PyMuPDF
import cairosvg

# Windows only
try:
    import pythoncom
    import win32com.client
except ImportError:
    pass

def convert_image(input_path, output_path, format):
    ext = os.path.splitext(input_path)[1].lower()
    if ext == '.svg':
        if format == 'png':
            cairosvg.svg2png(url=input_path, write_to=output_path)
        elif format == 'pdf':
            cairosvg.svg2pdf(url=input_path, write_to=output_path)
        elif format == 'jpg':
            tmp_png = output_path.replace('.jpg', '.png')
            cairosvg.svg2png(url=input_path, write_to=tmp_png)
            with Image.open(tmp_png) as img:
                img.convert('RGB').save(output_path, format='JPEG')
            os.remove(tmp_png)
        else:
            raise ValueError("Unsupported SVG target format.")
    else:
        with Image.open(input_path) as img:
            if format == 'jpg':
                img.convert('RGB').save(output_path, 'JPEG')
            else:
                img.save(output_path, format=format.upper())

def convert_dwg_to_pdf(dwg_path, pdf_output_path):
    pythoncom.CoInitialize()
    acad = win32com.client.Dispatch("AutoCAD.Application")
    acad.Visible = False
    doc = acad.Documents.Open(dwg_path)
    doc.SetVariable("BACKGROUNDPLOT", 0)

    dsd_path = os.path.splitext(dwg_path)[0] + ".dsd"
    dsd_content = f"""[DWF6Version]
Ver=1
[DWF6MinorVersion]
MinorVer=1
[Sheet1]
DWG={dwg_path}
Layout=*
OriginalSheetPath={dwg_path}
Has PlotStyles=0
[Target]
Type=6
DWF={pdf_output_path}
OUT={os.path.dirname(pdf_output_path)}
PWD=
[AutoCAD Block Data]
IncludeLayer=TRUE
PromptForDwfName=FALSE
RememberSheetSet=FALSE
"""
    with open(dsd_path, "w", encoding="utf-8") as f:
        f.write(dsd_content)

    acad.Publish.PublishToWeb(dsd_path)
    doc.Close(False)
    acad.Quit()
    pythoncom.CoUninitialize()