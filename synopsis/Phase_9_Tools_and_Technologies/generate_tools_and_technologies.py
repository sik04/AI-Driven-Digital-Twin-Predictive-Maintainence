import os
import subprocess
import zipfile

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
DIR = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(DIR, "tools_and_technologies.html")
PDF_PATH = os.path.join(DIR, "tools_and_technologies.pdf")
DOCX_PATH = os.path.join(DIR, "tools_and_technologies.docx")

def build_pdf():
    if not os.path.exists(CHROME_PATH):
        raise FileNotFoundError(f"Chrome not found at {CHROME_PATH}")
    html_uri = f"file:///{HTML_PATH.replace(os.sep, '/')}"
    cmd = [
        CHROME_PATH,
        "--headless=new",
        "--no-sandbox",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={PDF_PATH}",
        html_uri
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if res.returncode != 0 or not os.path.exists(PDF_PATH):
        raise RuntimeError(f"Chrome PDF generation failed: {res.stderr}")
    print(f"Generated PDF: {PDF_PATH} ({os.path.getsize(PDF_PATH)} bytes)")

def build_docx():
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>"""

    package_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

    doc_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""

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
    <w:pPrDefault>
      <w:pPr>
        <w:spacing w:line="360" w:lineRule="auto" w:after="200"/>
        <w:jc w:val="both"/>
      </w:pPr>
    </w:pPrDefault>
  </w:docDefaults>
</w:styles>"""

    def p(text, is_bold=False, is_italic=False, size=24, align="both", space_after=200):
        b_tag = "<w:b/>" if is_bold else ""
        i_tag = "<w:i/>" if is_italic else ""
        xml_text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return f"""    <w:p>
      <w:pPr>
        <w:jc w:val="{align}"/>
        <w:spacing w:line="360" w:lineRule="auto" w:after="{space_after}"/>
      </w:pPr>
      <w:r>
        <w:rPr>{b_tag}{i_tag}<w:sz w:val="{size}"/></w:rPr>
        <w:t xml:space="preserve">{xml_text}</w:t>
      </w:r>
    </w:p>"""

    def li(bullet_str, bold_prefix, text, indent=720):
        xml_bullet = bullet_str.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        xml_bold = bold_prefix.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        xml_text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return f"""    <w:p>
      <w:pPr>
        <w:ind w:left="{indent}" w:hanging="360"/>
        <w:jc w:val="both"/>
        <w:spacing w:line="360" w:lineRule="auto" w:after="120"/>
      </w:pPr>
      <w:r>
        <w:rPr><w:b/><w:sz w:val="24"/></w:rPr>
        <w:t xml:space="preserve">{xml_bullet} </w:t>
      </w:r>
      <w:r>
        <w:rPr><w:b/><w:sz w:val="24"/></w:rPr>
        <w:t xml:space="preserve">{xml_bold} </w:t>
      </w:r>
      <w:r>
        <w:rPr><w:sz w:val="24"/></w:rPr>
        <w:t xml:space="preserve">{xml_text}</w:t>
      </w:r>
    </w:p>"""

    def table_xml(headers, rows, widths=None):
        total_width = 8306  # available dxa on A4 with 1.5" left and 1.0" right margins
        if not widths:
            col_w = total_width // len(headers)
            widths = [col_w] * len(headers)
            widths[-1] = total_width - sum(widths[:-1])

        out = []
        out.append("    <w:tbl>")
        out.append("""      <w:tblPr>
        <w:tblW w:w="8306" w:type="dxa"/>
        <w:tblBorders>
          <w:top w:val="single" w:sz="12" w:space="0" w:color="000000"/>
          <w:bottom w:val="single" w:sz="12" w:space="0" w:color="000000"/>
          <w:left w:val="none"/>
          <w:right w:val="none"/>
          <w:insideH w:val="single" w:sz="4" w:space="0" w:color="E0E0E0"/>
          <w:insideV w:val="none"/>
        </w:tblBorders>
        <w:tblCellMar>
          <w:top w:w="100" w:type="dxa"/>
          <w:bottom w:w="100" w:type="dxa"/>
          <w:left w:w="120" w:type="dxa"/>
          <w:right w:w="120" w:type="dxa"/>
        </w:tblCellMar>
      </w:tblPr>""")

        out.append("      <w:tblGrid>")
        for w in widths:
            out.append(f'        <w:gridCol w:w="{w}"/>')
        out.append("      </w:tblGrid>")

        # Header Row
        out.append("      <w:tr>")
        out.append("""        <w:trPr>
          <w:tblHeader/>
          <w:cantSplit/>
        </w:trPr>""")
        for idx, h in enumerate(headers):
            xml_h = h.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            w = widths[idx]
            out.append(f"""        <w:tc>
          <w:tcPr>
            <w:tcW w:w="{w}" w:type="dxa"/>
            <w:shd w:val="clear" w:color="auto" w:fill="F2F2F2"/>
            <w:tcBorders>
              <w:bottom w:val="single" w:sz="8" w:space="0" w:color="000000"/>
            </w:tcBorders>
          </w:tcPr>
          <w:p>
            <w:pPr><w:spacing w:line="240" w:lineRule="auto" w:after="0"/><w:jc w:val="left"/></w:pPr>
            <w:r><w:rPr><w:b/><w:sz w:val="18"/></w:rPr><w:t xml:space="preserve">{xml_h}</w:t></w:r>
          </w:p>
        </w:tc>""")
        out.append("      </w:tr>")

        # Data Rows
        for r in rows:
            out.append("      <w:tr>")
            out.append("        <w:trPr><w:cantSplit/></w:trPr>")
            for idx, val in enumerate(r):
                xml_val = str(val).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                w = widths[idx]
                out.append(f"""        <w:tc>
          <w:tcPr>
            <w:tcW w:w="{w}" w:type="dxa"/>
          </w:tcPr>
          <w:p>
            <w:pPr><w:spacing w:line="240" w:lineRule="auto" w:after="0"/><w:jc w:val="left"/></w:pPr>
            <w:r><w:rPr><w:sz w:val="18"/></w:rPr><w:t xml:space="preserve">{xml_val}</w:t></w:r>
          </w:p>
        </w:tc>""")
            out.append("      </w:tr>")

        out.append("    </w:tbl>")
        out.append("""    <w:p><w:pPr><w:spacing w:line="240" w:lineRule="auto" w:after="160"/></w:pPr></w:p>""")
        return "\n".join(out)

    body_elements = []

    # Section 9 Title
    body_elements.append(p("9. Tools, Technologies and System Requirements", is_bold=True, size=28, space_after=300))

    # 9.1
    body_elements.append(p("9.1 Programming Language and Runtime Environment", is_bold=True, size=24, space_after=160))
    body_elements.append(p(
        "The IntelliTwin framework is implemented entirely in the Python programming language, utilizing modern, type-annotated "
        "CPython runtimes (Python 3.10, 3.11, 3.12, and 3.13) [1]–[3]. Python was chosen as the primary scientific computing foundation "
        "due to its mature mathematical ecosystem, extensive deep learning and ensemble regression libraries, and robust web service frameworks [2], [4]."
    ))
    body_elements.append(p("Dependency Management and Environment Isolation", is_bold=True, is_italic=True, size=24, space_after=120))
    body_elements.append(p("To guarantee reproducible execution across heterogeneous operating environments, dependency resolution is governed through modern Python packaging standards (PEP 517, PEP 518, and PEP 621) formalized in pyproject.toml:"))
    body_elements.append(li(
        "•", "Isolated Virtual Environments:",
        "Isolated execution sandboxes are provisioned using Python's native venv module, preventing conflicting global library bindings."
    ))
    body_elements.append(li(
        "•", "Deterministic Build Backend:",
        "The packaging backend utilizes setuptools (≥ 61.0) with editable source installation (pip install -e \".[dev,research]\"), ensuring modular packaging of the src/intellitwin/ namespace."
    ))
    body_elements.append(li(
        "•", "Cross-Platform Portability:",
        "The runtime workflow is validated across Microsoft Windows 11 (PowerShell), Ubuntu Linux (20.04/22.04 LTS), and macOS (POSIX/Darwin)."
    ))
    body_elements.append(li(
        "•", "Source Line-Ending Normalization (sha256-utf8-lf-v1):",
        "To guarantee identical cryptographic source hashes across Windows (CRLF) and Linux (LF), all code provenance digests normalize text to UTF-8 Unix line feeds (\\n) prior to hashing, resolving cross-platform Git checkout discrepancies (ADR-022)."
    ))

    # 9.2
    body_elements.append(p("9.2 Core Frameworks and Scientific Computing Libraries", is_bold=True, size=24, space_after=160))
    body_elements.append(p("The scientific architecture of IntelliTwin integrates established machine learning, deep learning, statistical inference, and numerical processing libraries:"))

    body_elements.append(p("1. Machine Learning and Deep Learning Stack", is_bold=True, is_italic=True, size=24, space_after=120))
    body_elements.append(li(
        "•", "PyTorch (≥ 2.2):",
        "Serves as the primary deep learning framework for the temporal sequence prognostic engine. Houses the deep Bidirectional LSTM architecture with two recurrent layers (h = 64 hidden units), variational dropout (p = 0.20), and a LeakyReLU projection head. Supports both CUDA-accelerated GPU tensor computations and CPU fallback execution with deterministic seed control [3], [4]."
    ))
    body_elements.append(li(
        "•", "Scikit-Learn (≥ 1.2.0):",
        "Provides the shallow ensemble regression and clustering foundation. Powers the HistGradientBoostingRegressor base models optimizing asymmetric pinball loss functions (ρ ∈ {0.05, 0.50, 0.95}) over flattened 510-dimensional feature representations. Implements K-means clustering (K = 6) for operating regime stratification and training-only feature scalers [1], [10]."
    ))

    body_elements.append(p("2. Numerical Processing and Data Manipulation Stack", is_bold=True, is_italic=True, size=24, space_after=120))
    body_elements.append(li(
        "•", "NumPy (≥ 1.24.0):",
        "Provides vector and matrix operations for the 30-cycle causal sliding lookback windowing (W = 30), array reshaping (C-order row-major flattening), and element-wise array operations."
    ))
    body_elements.append(li(
        "•", "Pandas (≥ 2.0.0):",
        "Handles tabular ingestion of NASA C-MAPSS telemetry text streams, metadata alignment, engine-level split manifests, and cycle-by-cycle trajectory records [1]."
    ))
    body_elements.append(li(
        "•", "SciPy (≥ 1.10.0):",
        "Supports statistical bootstrapping, cluster sampling, and empirical probability distribution calculations."
    ))
    body_elements.append(li(
        "•", "Fractions Standard Module (fractions.Fraction):",
        "Executes exact rational arithmetic for the engine-weighted conformal quantile solver, avoiding floating-point roundoff errors during empirical CDF threshold evaluation [9]."
    ))

    # Table 9.1
    body_elements.append(p("Table 9.1: Core Scientific Computing and Machine Learning Toolchain", is_bold=True, size=20, space_after=100))
    t1_headers = ["Library / Tool", "Version", "Functional Role in IntelliTwin Framework"]
    t1_rows = [
        ["Python", "3.10–3.13", "Core programming language and runtime execution environment"],
        ["PyTorch", "≥ 2.2.0", "Deep bidirectional LSTM sequence modeling, GPU/CPU tensor graphs"],
        ["Scikit-Learn", "≥ 1.2.0", "HistGradientBoosting multi-quantile regressors, K-means regime clustering"],
        ["NumPy", "≥ 1.24.0", "High-dimensional causal array buffering, C-order flattening (510-dim)"],
        ["Pandas", "≥ 2.0.0", "C-MAPSS telemetry ingestion, engine split manifests, event logs"],
        ["SciPy", "≥ 1.10.0", "Statistical bootstrap resamplers, confidence interval estimators"],
        ["FastAPI", "≥ 0.110.0", "Asynchronous REST API serving Digital Twin replay sessions"],
        ["Uvicorn", "≥ 0.28.0", "High-performance ASGI production server hosting REST endpoints"],
        ["Pytest", "≥ 7.4.0", "Test automation suite spanning 37 unit and integration modules"],
        ["Ruff", "≥ 0.1.0", "High-speed code linter and PEP 8 formatter"],
        ["Mypy", "≥ 1.5.0", "Strict static type checker verifying type safety across src/"]
    ]
    t1_widths = [1800, 1400, 5106]
    body_elements.append(table_xml(t1_headers, t1_rows, t1_widths))

    # 9.3
    body_elements.append(p("9.3 Digital Twin Simulation, API, and Visualization Stack", is_bold=True, size=24, space_after=160))
    body_elements.append(p(
        "The operational prototype of IntelliTwin bridges scientific algorithms and interactive monitoring via a lightweight, "
        "production-ready web technology stack adhering to ISO 23247 principles [2], [13], [14]:"
    ))
    body_elements.append(li(
        "•", "FastAPI Backend Service (≥ 0.110.0):",
        "A high-performance Python web framework based on Starlette and Pydantic. Exposes RESTful endpoints for session initialization, cycle advancement, resetting, catalog discovery, and trace export (/api/sessions, /advance, /reset, /trace.csv). Employs asynchronous request routing and strict schema validation [2]."
    ))
    body_elements.append(li(
        "•", "Uvicorn ASGI Server (≥ 0.28.0):",
        "Serves the FastAPI application asynchronously on local port 8000 with low latency and high concurrency."
    ))
    body_elements.append(li(
        "•", "Thread-Safe Replay Engine:",
        "Built on Python's threading.Lock primitives, guaranteeing mutually exclusive, cycle-by-cycle telemetry consumption and preventing race conditions during live streaming."
    ))
    body_elements.append(li(
        "•", "Frontend Operator Dashboard (apps/twin_dashboard/):",
        "Implemented in modern HTML5, CSS3, and vanilla JavaScript (ES6+). Provides dynamic sensor time-series charts, RUL prediction intervals with confidence bands, gauge dials for Health Index, and multi-stage visual alert banners (NOMINAL, ADVISORY, CRITICAL_INTERVENTION)."
    ))

    # 9.4
    body_elements.append(p("9.4 Development Toolchain, Quality Assurance, and Testing Framework", is_bold=True, size=24, space_after=160))
    body_elements.append(p("To ensure commercial-grade software quality, maintainability, and scientific auditability, the repository enforces an automated development toolchain:"))
    body_elements.append(li(
        "•", "Code Quality and Formatting (ruff):",
        "The ruff linter and formatter enforces strict code style adherence to PEP 8, sorting imports with isort, and automatically fixing safe code anomalies. Line length is strictly limited to 100 characters."
    ))
    body_elements.append(li(
        "•", "Static Type Analysis (mypy):",
        "Strict static type checking (strict = true) is enforced across all modules in src/intellitwin/, ensuring complete type safety for function signatures, array dimensions, and data structures."
    ))
    body_elements.append(li(
        "•", "Automated Test Suite (pytest):",
        "An automated suite of 37 pytest modules validates causal window boundaries, model training and checkpoint determinism, rational conformal quantiles, maintenance cost simulation in SCU, and digital twin replay parity (atol ≤ 10^-4)."
    ))
    body_elements.append(li(
        "•", "Cryptographic Provenance Engine (src/intellitwin/provenance.py):",
        "Interrogates the host system to capture execution metadata, package versions, random seeds, and Git commit hashes. Enforces a git-clean check (git_dirty: false) before permitting formal audit or confirmatory experiment execution."
    ))

    # 9.5
    body_elements.append(p("9.5 Hardware and Operational System Requirements", is_bold=True, size=24, space_after=160))
    body_elements.append(p(
        "The IntelliTwin framework is engineered for high computational efficiency, running effectively on standard commodity developer workstations "
        "as well as high-performance compute clusters."
    ))

    # Table 9.2
    body_elements.append(p("Table 9.2: Minimum and Recommended System Hardware Specifications", is_bold=True, size=20, space_after=100))
    t2_headers = ["Hardware Component", "Minimum Development Specification", "Recommended Research / Cluster Specification"]
    t2_rows = [
        ["Processor (CPU)", "Quad-core Intel Core i5 / AMD Ryzen 5 (2.0 GHz+)", "8+ cores (Intel Core i7/i9, AMD Ryzen 7/9, Apple M2/M3)"],
        ["System Memory (RAM)", "8 GB DDR4", "16–32 GB DDR4/DDR5 (for 10,000 bootstrap resamples)"],
        ["Storage (SSD)", "10 GB free space (NVMe or SATA SSD)", "25 GB free space (NVMe SSD for fast checkpoint I/O)"],
        ["Graphics (GPU)", "Integrated GPU (CPU fallback supported)", "NVIDIA GPU with CUDA (≥ 8 GB VRAM, RTX 3060+)"],
        ["Operating System", "Windows 10/11 (64-bit), Ubuntu 20.04+, macOS 12+", "Ubuntu Linux 22.04 LTS (64-bit x86_64)"],
        ["Network Interface", "Standard loopback interface for local REST API", "Gigabit Ethernet for distributed cluster nodes"]
    ]
    t2_widths = [2000, 3106, 3200]
    body_elements.append(table_xml(t2_headers, t2_rows, t2_widths))

    body_elements.append(p("Physical Boundary Demarcation", is_bold=True, is_italic=True, size=24, space_after=120))
    body_elements.append(p(
        "Because IntelliTwin is formulated as an offline, trace-driven research prototype utilizing NASA C-MAPSS run-to-failure telemetry [1], "
        "no specialized physical avionics test benches, ARINC 429 databuses, or embedded edge microcontrollers (e.g., STM32, ESP32) are required for execution. "
        "Telemetry ingestion is entirely software-driven via the TwinReplayEngine streaming buffer."
    ))

    # 9.6
    body_elements.append(p("9.6 Institutional Software Compliance and Authoring Standards", is_bold=True, size=24, space_after=160))
    body_elements.append(p("In compliance with the official guidelines of the Department of Information Technology at Ajay Kumar Garg Engineering College (Circular AKGEC/IT/CSIT/26-27/PROJ-m):"))
    body_elements.append(li(
        "•", "Authoring Environment:",
        "The project synopsis is authored exclusively using Overleaf (LaTeX) utilizing the standard institutional template structure."
    ))
    body_elements.append(li(
        "•", "Typography and Geometry:",
        "Adheres to standard A4 page dimensions (210 × 297 mm), margins (Left: 1.5\", Top/Bottom/Right: 1.0\"), Times New Roman typeface (14pt bold section headings, 12pt bold subheadings, 12pt regular body), and 1.5 line spacing."
    ))
    body_elements.append(li(
        "•", "Citation Format:",
        "Bibliographic references follow IEEE numerical bracketed citation standards [1]–[14]."
    ))
    body_elements.append(li(
        "•", "Deterministic Multi-Format Tooling:",
        "Companion Python automation scripts generate bit-for-bit identical, publication-quality Microsoft Word (.docx) and PDF (.pdf) artifacts across platforms."
    ))

    # References
    body_elements.append(p("References", is_bold=True, size=24, space_after=160))
    refs = [
        "[1] A. Saxena, K. Goebel, D. Simon, and N. Eklund, \"Damage propagation modeling for aircraft engine run-to-failure simulation,\" in Proc. 2008 Int. Conf. Prognostics and Health Management (PHM), IEEE, 2008, pp. 1–9.",
        "[2] Z. Huang, Y. Shen, J. Li, M. Fey, and C. Brecher, \"A survey on AI-driven digital twins in Industry 4.0: Smart manufacturing and advanced robotics,\" Sensors, vol. 21, no. 19, p. 6340, 2021.",
        "[3] R. Diao, M. Zhou, G. Meng, and S. Wang, \"Turbofan engine remaining useful life prediction with reliable prediction intervals via LSTM-based quantile regression and conformal calibration,\" Sensors, vol. 26, no. 7, p. 2249, 2026.",
        "[4] A. Javanmardi and E. Hüllermeier, \"Conformal prediction intervals for remaining useful lifetime estimation,\" Int. J. Progn. Health Manag., vol. 14, no. 2, pp. 1–14, 2023.",
        "[5] Z. Zhu, L. Wang, M. Chen, and X. Zhao, \"Predictive maintenance strategies for aero-engines considering remaining useful life prediction interval,\" Qual. Reliab. Eng. Int., 2025, doi: 10.1002/qre.70043.",
        "[6] C. Chen, J. Shi, N. Lu, Z. H. Zhu, and B. Jiang, \"Data-driven predictive maintenance strategy considering the uncertainty in remaining useful life prediction,\" Neurocomputing, vol. 494, pp. 79–88, 2022.",
        "[7] S. Cortes-Gomez, C. M. Patiño, Y. Byun, S. Wu, E. Horvitz, and B. Wilder, \"Utility-directed conformal prediction: A decision-aware framework for actionable uncertainty quantification,\" in Int. Conf. Learn. Represent. (ICLR), 2025.",
        "[8] G. K. Walia and M. Kumar, \"Uncertainty-aware remaining useful life prediction and PPO based optimal maintenance scheduling in industrial IoT,\" Reliab. Eng. Syst. Saf., p. 112356, 2026.",
        "[9] Y. Lee, R. F. Barber, and R. Willett, \"Distribution-free inference with hierarchical data,\" arXiv preprint arXiv:2306.06342, 2023.",
        "[10] C. D. Robinson, \"Remaining useful life estimation for aircraft engines with risk-aware prediction intervals via conformalized quantile regression,\" Int. J. Progn. Health Manag., vol. 17, no. 1, p. 4724, 2026.",
        "[11] T. Gneiting and A. E. Raftery, \"Strictly proper scoring rules, prediction, and estimation,\" J. Am. Stat. Assoc., vol. 102, no. 477, pp. 359–378, 2007.",
        "[12] D. Lakens, \"Equivalence tests: A practical primer for t tests, correlations, and meta-analyses,\" Soc. Psychol. Personal. Sci., vol. 8, no. 4, pp. 355–362, 2017.",
        "[13] J. Wu, Y. Zhou, X. Wang, C. Chen, Y. Ma, and C. Zhang, \"Research on remaining useful life prediction of equipment based on digital twins,\" Sensors, vol. 26, no. 4, p. 1240, 2026.",
        "[14] ISO 23247-1:2021, \"Automation systems and integration — Digital twin framework for manufacturing — Part 1: Overview and general principles,\" International Organization for Standardization, Geneva, Switzerland, 2021."
    ]
    for r in refs:
        body_elements.append(p(r, size=20, align="left", space_after=100))

    document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
{chr(10).join(body_elements)}
    <w:sectPr>
      <w:pgSz w:w="11906" w:h="16838"/>
      <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="2160" w:header="720" w:footer="720" w:gutter="0"/>
    </w:sectPr>
  </w:body>
</w:document>"""

    fixed_time = (2026, 11, 1, 0, 0, 0)
    with zipfile.ZipFile(DOCX_PATH, "w") as z:
        for arcname, data in [
            ("[Content_Types].xml", content_types),
            ("_rels/.rels", package_rels),
            ("word/_rels/document.xml.rels", doc_rels),
            ("word/styles.xml", styles_xml),
            ("word/document.xml", document_xml)
        ]:
            zinfo = zipfile.ZipInfo(arcname, date_time=fixed_time)
            zinfo.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(zinfo, data)

    print(f"Generated DOCX: {DOCX_PATH} ({os.path.getsize(DOCX_PATH)} bytes)")

if __name__ == "__main__":
    build_pdf()
    build_docx()
