"""
Title Page Generator for IntelliTwin Project Synopsis
Generates both official A4 PDF and DOCX formats following AKGEC IT Department guidelines.
"""

import os
import struct
import zlib
import zipfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PNG = os.path.join(SCRIPT_DIR, "akgec_logo.png")
OUTPUT_PDF = os.path.join(SCRIPT_DIR, "title_page.pdf")
OUTPUT_DOCX = os.path.join(SCRIPT_DIR, "title_page.docx")

# Approximate glyph widths for Times-Roman and Times-Bold (1000 units per em)
def get_char_width(char, is_bold=False):
    if char == ' ':
        return 250
    if char in 'ijl.,:;!\'':
        return 278
    if char in 'frtI':
        return 333
    if char in '()[]-':
        return 333
    if char in 'abcdeghknopqsuvxyz':
        return 500 if not is_bold else 550
    if char in '0123456789':
        return 500 if not is_bold else 550
    if char in 'ABCDEFGHJKLNPQRSTUVXYZ':
        return 722 if not is_bold else 750
    if char in 'mw':
        return 750 if not is_bold else 800
    if char in 'MO':
        return 800 if not is_bold else 850
    if char in 'W':
        return 944 if not is_bold else 1000
    return 600

def string_width(text, size, is_bold=False):
    return sum(get_char_width(c, is_bold) for c in text) * (size / 1000.0)

def escape_pdf_string(s):
    return s.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')

def build_pdf():
    # Read logo image dimensions and pixel bytes
    # Logo is 204 x 192 RGB PNG
    with open(LOGO_PNG, "rb") as f:
        png_data = f.read()

    # Parse PNG chunks to get raw RGB
    pos = 8
    img_w, img_h = 204, 192
    idat_chunks = bytearray()
    while pos < len(png_data):
        chunk_len = struct.unpack(">I", png_data[pos:pos+4])[0]
        chunk_type = png_data[pos+4:pos+8]
        if chunk_type == b'IHDR':
            img_w, img_h = struct.unpack(">II", png_data[pos+8:pos+16])
        elif chunk_type == b'IDAT':
            idat_chunks.extend(png_data[pos+8:pos+8+chunk_len])
        elif chunk_type == b'IEND':
            break
        pos += 12 + chunk_len

    raw_decomp = zlib.decompress(bytes(idat_chunks))
    # Unfilter PNG scanlines (filter type 0 = None)
    raw_rgb = bytearray()
    stride = img_w * 3 + 1
    for y in range(img_h):
        line = raw_decomp[y * stride + 1 : (y + 1) * stride]
        raw_rgb.extend(line)

    img_stream_compressed = zlib.compress(bytes(raw_rgb))

    # Page layout: A4 (595.28 x 841.89 pt)
    # Margins: Left 1.5 in (108 pt), Right 1.0 in (72 pt), Top 1.0 in (72 pt), Bottom 1.0 in (72 pt)
    # Printable area: X from 108 to 523.28 (width 415.28 pt)
    # Center X = 108 + 415.28 / 2 = 315.64 pt
    center_x = 315.64
    right_x = 523.28

    content_ops = []

    def add_line(text, size, y, is_bold=False, align="center"):
        font_tag = "/F1" if is_bold else "/F2"
        w = string_width(text, size, is_bold)
        if align == "center":
            x = center_x - (w / 2.0)
        elif align == "right":
            x = right_x - w
        else:
            x = 108.0
        escaped = escape_pdf_string(text)
        content_ops.append(f"BT {font_tag} {size:.1f} Tf 1 0 0 1 {x:.2f} {y:.2f} Tm ({escaped}) Tj ET\n")

    # Group ID at top right
    add_line("Project Group ID: CSIT 4 2023-27/IT/SECTION/GID", 10.5, 765.0, is_bold=True, align="right")

    # Heading
    add_line("A PROJECT SYNOPSIS ON", 14.0, 715.0, is_bold=True, align="center")

    # Project Title (18 pt Bold, 2 lines)
    add_line("IntelliTwin: AI-Driven Digital Twin Framework", 17.5, 665.0, is_bold=True, align="center")
    add_line("for Predictive Maintenance", 17.5, 642.0, is_bold=True, align="center")

    # Submission statement
    add_line("Submitted", 12.0, 595.0, is_bold=False, align="center")
    add_line("for the fulfillment of the award of", 12.0, 580.0, is_bold=False, align="center")
    add_line("Bachelor of Technology in", 13.0, 562.0, is_bold=True, align="center")
    add_line("Information Technology", 13.0, 545.0, is_bold=True, align="center")

    # Team members
    add_line("by", 12.0, 510.0, is_bold=True, align="center")
    add_line("Shiksha Pandey (2300270110112)", 12.0, 488.0, is_bold=True, align="center")
    add_line("Mayank Singh (2300270310115)", 12.0, 470.0, is_bold=True, align="center")

    # Guide
    add_line("Under the guidance of", 12.0, 432.0, is_bold=False, align="center")
    add_line("Dr. Ruchi Gupta", 14.0, 412.0, is_bold=True, align="center")

    # Logo Placement: width=80 pt, height=75.3 pt, centered
    logo_w = 80.0
    logo_h = 75.29
    logo_x = center_x - (logo_w / 2.0)
    logo_y = 305.0
    content_ops.append(f"q {logo_w:.2f} 0 0 {logo_h:.2f} {logo_x:.2f} {logo_y:.2f} cm /Im1 Do Q\n")

    # Institutional Affiliation
    add_line("Department of Information Technology", 12.0, 275.0, is_bold=True, align="center")
    add_line("AJAY KUMAR GARG ENGINEERING COLLEGE, GHAZIABAD", 13.0, 255.0, is_bold=True, align="center")
    add_line("DR. A.P.J. ABDUL KALAM TECHNICAL UNIVERSITY, LUCKNOW", 11.0, 238.0, is_bold=True, align="center")

    # Academic Session
    add_line("Academic Session: 2026-27", 12.0, 202.0, is_bold=True, align="center")

    contents_str = "".join(content_ops).encode("latin1")

    # Assemble PDF Objects
    objects = []

    # Obj 1: Catalog
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    # Obj 2: Pages
    objects.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    # Obj 3: Page
    objects.append(
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595.28 841.89] "
        b"/Contents 4 0 R "
        b"/Resources << "
        b"/Font << /F1 5 0 R /F2 6 0 R >> "
        b"/XObject << /Im1 7 0 R >> "
        b">> >>"
    )
    # Obj 4: Contents
    objects.append(
        f"<< /Length {len(contents_str)} >>\nstream\n".encode("latin1")
        + contents_str
        + b"\nendstream"
    )
    # Obj 5: Font F1 (Times-Bold)
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Times-Bold /Encoding /WinAnsiEncoding >>")
    # Obj 6: Font F2 (Times-Roman)
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Times-Roman /Encoding /WinAnsiEncoding >>")
    # Obj 7: XObject Image
    objects.append(
        f"<< /Type /XObject /Subtype /Image /Width {img_w} /Height {img_h} "
        f"/ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /FlateDecode /Length {len(img_stream_compressed)} >>\nstream\n".encode("latin1")
        + img_stream_compressed
        + b"\nendstream"
    )

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for i, obj in enumerate(objects):
        offsets.append(len(pdf))
        pdf.extend(f"{i+1} 0 obj\n".encode("latin1"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")

    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects)+1}\n".encode("latin1"))
    pdf.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        pdf.extend(f"{off:010d} 00000 n \n".encode("latin1"))

    pdf.extend(
        f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("latin1")
    )

    with open(OUTPUT_PDF, "wb") as f:
        f.write(pdf)
    print(f"Generated PDF: {OUTPUT_PDF} ({len(pdf)} bytes)")

def build_docx():
    # Build complete OpenXML DOCX archive
    with open(LOGO_PNG, "rb") as f:
        logo_bytes = f.read()

    # Content Types
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Default Extension="png" ContentType="image/png"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>"""

    # Package Relationships
    package_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

    # Document Relationships
    doc_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image1.png"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""

    # Styles
    styles_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:docDefaults>
    <w:rPrDefault>
      <w:rPr>
        <w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/>
        <w:sz w:val="24"/>
        <w:color w:val="000000"/>
      </w:rPr>
    </w:rPrDefault>
  </w:docDefaults>
</w:styles>"""

    # Document body
    # Margins: Left 1.5 in = 2160 dxa, Right 1.0 in = 1440 dxa, Top 1.0 in = 1440 dxa, Bottom 1.0 in = 1440 dxa
    # Page size: A4 (11906 x 16838 dxa)
    document_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
            xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
            xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
            xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
            xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">
  <w:body>
    <!-- Group ID at Top Right -->
    <w:p>
      <w:pPr>
        <w:jc w:val="right"/>
        <w:spacing w:after="360" w:line="240" w:lineRule="auto"/>
      </w:pPr>
      <w:r>
        <w:rPr><w:b/><w:sz w:val="21"/></w:rPr>
        <w:t>Project Group ID: CSIT 4 2023-27/IT/SECTION/GID</w:t>
      </w:r>
    </w:p>

    <!-- Heading -->
    <w:p>
      <w:pPr>
        <w:jc w:val="center"/>
        <w:spacing w:after="280" w:line="240" w:lineRule="auto"/>
      </w:pPr>
      <w:r>
        <w:rPr><w:b/><w:sz w:val="28"/></w:rPr>
        <w:t>A PROJECT SYNOPSIS ON</w:t>
      </w:r>
    </w:p>

    <!-- Project Title -->
    <w:p>
      <w:pPr>
        <w:jc w:val="center"/>
        <w:spacing w:after="120" w:line="320" w:lineRule="auto"/>
      </w:pPr>
      <w:r>
        <w:rPr><w:b/><w:sz w:val="36"/></w:rPr>
        <w:t>IntelliTwin: AI-Driven Digital Twin Framework</w:t>
      </w:r>
    </w:p>
    <w:p>
      <w:pPr>
        <w:jc w:val="center"/>
        <w:spacing w:after="320" w:line="320" w:lineRule="auto"/>
      </w:pPr>
      <w:r>
        <w:rPr><w:b/><w:sz w:val="36"/></w:rPr>
        <w:t>for Predictive Maintenance</w:t>
      </w:r>
    </w:p>

    <!-- Submission Statement -->
    <w:p>
      <w:pPr>
        <w:jc w:val="center"/>
        <w:spacing w:after="60" w:line="260" w:lineRule="auto"/>
      </w:pPr>
      <w:r>
        <w:rPr><w:i/><w:sz w:val="24"/></w:rPr>
        <w:t>Submitted</w:t>
      </w:r>
    </w:p>
    <w:p>
      <w:pPr>
        <w:jc w:val="center"/>
        <w:spacing w:after="60" w:line="260" w:lineRule="auto"/>
      </w:pPr>
      <w:r>
        <w:rPr><w:i/><w:sz w:val="24"/></w:rPr>
        <w:t>for the fulfillment of the award of</w:t>
      </w:r>
    </w:p>
    <w:p>
      <w:pPr>
        <w:jc w:val="center"/>
        <w:spacing w:after="60" w:line="280" w:lineRule="auto"/>
      </w:pPr>
      <w:r>
        <w:rPr><w:b/><w:sz w:val="26"/></w:rPr>
        <w:t>Bachelor of Technology in</w:t>
      </w:r>
    </w:p>
    <w:p>
      <w:pPr>
        <w:jc w:val="center"/>
        <w:spacing w:after="280" w:line="280" w:lineRule="auto"/>
      </w:pPr>
      <w:r>
        <w:rPr><w:b/><w:sz w:val="26"/></w:rPr>
        <w:t>Information Technology</w:t>
      </w:r>
    </w:p>

    <!-- Team Members -->
    <w:p>
      <w:pPr>
        <w:jc w:val="center"/>
        <w:spacing w:after="100" w:line="240" w:lineRule="auto"/>
      </w:pPr>
      <w:r>
        <w:rPr><w:b/><w:sz w:val="24"/></w:rPr>
        <w:t>by</w:t>
      </w:r>
    </w:p>
    <w:p>
      <w:pPr>
        <w:jc w:val="center"/>
        <w:spacing w:after="60" w:line="260" w:lineRule="auto"/>
      </w:pPr>
      <w:r>
        <w:rPr><w:b/><w:sz w:val="24"/></w:rPr>
        <w:t>Shiksha Pandey (2300270110112)</w:t>
      </w:r>
    </w:p>
    <w:p>
      <w:pPr>
        <w:jc w:val="center"/>
        <w:spacing w:after="280" w:line="260" w:lineRule="auto"/>
      </w:pPr>
      <w:r>
        <w:rPr><w:b/><w:sz w:val="24"/></w:rPr>
        <w:t>Mayank Singh (2300270310115)</w:t>
      </w:r>
    </w:p>

    <!-- Guide -->
    <w:p>
      <w:pPr>
        <w:jc w:val="center"/>
        <w:spacing w:after="60" w:line="240" w:lineRule="auto"/>
      </w:pPr>
      <w:r>
        <w:rPr><w:i/><w:sz w:val="24"/></w:rPr>
        <w:t>Under the guidance of</w:t>
      </w:r>
    </w:p>
    <w:p>
      <w:pPr>
        <w:jc w:val="center"/>
        <w:spacing w:after="240" w:line="260" w:lineRule="auto"/>
      </w:pPr>
      <w:r>
        <w:rPr><w:b/><w:sz w:val="28"/></w:rPr>
        <w:t>Dr. Ruchi Gupta</w:t>
      </w:r>
    </w:p>

    <!-- Emblem Image -->
    <w:p>
      <w:pPr>
        <w:jc w:val="center"/>
        <w:spacing w:after="200"/>
      </w:pPr>
      <w:r>
        <w:drawing>
          <wp:inline distT="0" distB="0" distL="0" distR="0">
            <wp:extent cx="1020000" cy="960000"/>
            <wp:docPr id="1" name="AKGEC Logo"/>
            <a:graphic>
              <a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">
                <pic:pic>
                  <pic:nvPicPr>
                    <pic:cNvPr id="0" name="akgec_logo.png"/>
                    <pic:cNvPicPr/>
                  </pic:nvPicPr>
                  <pic:blipFill>
                    <a:blip r:embed="rId1"/>
                    <a:stretch><a:fillRect/></a:stretch>
                  </pic:blipFill>
                  <pic:spPr>
                    <a:xfrm>
                      <a:off x="0" y="0"/>
                      <a:ext cx="1020000" cy="960000"/>
                    </a:xfrm>
                    <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
                  </pic:spPr>
                </pic:pic>
              </a:graphicData>
            </a:graphic>
          </wp:inline>
        </w:drawing>
      </w:r>
    </w:p>

    <!-- Institution and University -->
    <w:p>
      <w:pPr>
        <w:jc w:val="center"/>
        <w:spacing w:after="60" w:line="240" w:lineRule="auto"/>
      </w:pPr>
      <w:r>
        <w:rPr><w:b/><w:sz w:val="24"/></w:rPr>
        <w:t>Department of Information Technology</w:t>
      </w:r>
    </w:p>
    <w:p>
      <w:pPr>
        <w:jc w:val="center"/>
        <w:spacing w:after="60" w:line="260" w:lineRule="auto"/>
      </w:pPr>
      <w:r>
        <w:rPr><w:b/><w:sz w:val="26"/></w:rPr>
        <w:t>AJAY KUMAR GARG ENGINEERING COLLEGE, GHAZIABAD</w:t>
      </w:r>
    </w:p>
    <w:p>
      <w:pPr>
        <w:jc w:val="center"/>
        <w:spacing w:after="160" w:line="240" w:lineRule="auto"/>
      </w:pPr>
      <w:r>
        <w:rPr><w:b/><w:sz w:val="22"/></w:rPr>
        <w:t>DR. A.P.J. ABDUL KALAM TECHNICAL UNIVERSITY, LUCKNOW</w:t>
      </w:r>
    </w:p>

    <!-- Academic Session -->
    <w:p>
      <w:pPr>
        <w:jc w:val="center"/>
        <w:spacing w:after="0" w:line="240" w:lineRule="auto"/>
      </w:pPr>
      <w:r>
        <w:rPr><w:b/><w:sz w:val="24"/></w:rPr>
        <w:t>Academic Session: 2026–27</w:t>
      </w:r>
    </w:p>

    <w:sectPr>
      <w:pgSz w:w="11906" w:h="16838"/>
      <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="2160" w:header="720" w:footer="720" w:gutter="0"/>
    </w:sectPr>
  </w:body>
</w:document>"""

    with zipfile.ZipFile(OUTPUT_DOCX, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", package_rels)
        z.writestr("word/_rels/document.xml.rels", doc_rels)
        z.writestr("word/styles.xml", styles_xml)
        z.writestr("word/document.xml", document_xml)
        z.writestr("word/media/image1.png", logo_bytes)

    print(f"Generated DOCX: {OUTPUT_DOCX} ({os.path.getsize(OUTPUT_DOCX)} bytes)")

if __name__ == "__main__":
    build_pdf()
    build_docx()
