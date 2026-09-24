import os
import json
from pypdf import PdfReader

script_dir = os.path.dirname(os.path.abspath(__file__))
papers_dir = os.path.normpath(os.path.join(script_dir, "..", "papers"))

def get_text_from_pages(reader, page_indices):
    text = ""
    for idx in page_indices:
        if 0 <= idx < len(reader.pages):
            text += f"\n--- Page {idx+1} ---\n" + (reader.pages[idx].extract_text() or "")
    return text

detailed_analyses = {}

# 1. Paper 10: AI-Driven Digital Twins for Smart Urban Infrastructure
p10_reader = PdfReader(os.path.join(papers_dir, "paper 10.pdf"))
# Looking around pages 22-28
detailed_analyses["paper 10"] = {
    "title": "AI-Driven Digital Twins for Smart Urban Infrastructure: A Comparative Survey",
    "gaps_text": get_text_from_pages(p10_reader, range(22, min(28, len(p10_reader.pages))))
}

# 2. Paper 11: AI-Augmented Digital Twin Architecture for Predictive Maintenance
p11_reader = PdfReader(os.path.join(papers_dir, "paper 11.pdf"))
detailed_analyses["paper 11"] = {
    "title": "AI-Augmented Digital Twin Architecture for Predictive Maintenance in Smart Urban Infrastructure",
    "gaps_text": get_text_from_pages(p11_reader, range(10, len(p11_reader.pages)))
}

# 3. Paper 4: Thesis Hu Wei (Chapter 7: pages 155-165 approx, 0-indexed: 154 to 164)
p4_reader = PdfReader(os.path.join(papers_dir, "paper4.pdf"))
detailed_analyses["paper 4"] = {
    "title": "Hu Wei Thesis: Digital Twin and AI Enabled Predictive Maintenance in Building Industry",
    "gaps_text": get_text_from_pages(p4_reader, range(153, min(165, len(p4_reader.pages))))
}

# 4. Paper 8: Bridge DT Review
p8_reader = PdfReader(os.path.join(papers_dir, "paper 8.pdf"))
detailed_analyses["paper 8"] = {
    "title": "Evolution of Digital Twin Frameworks in Bridge Management: Review and Future Directions",
    "gaps_text": get_text_from_pages(p8_reader, range(28, min(35, len(p8_reader.pages))))
}

# 5. Paper 14: DT RUL prediction
p14_reader = PdfReader(os.path.join(papers_dir, "paper 14.pdf"))
detailed_analyses["paper 14"] = {
    "title": "DT-based Equipment RUL Prediction Using Ensemble Learning",
    "gaps_text": get_text_from_pages(p14_reader, range(20, min(24, len(p14_reader.pages))))
}

# 6. Paper 15: DT Federated Learning Anomaly Detection
p15_reader = PdfReader(os.path.join(papers_dir, "paper 15.pdf"))
detailed_analyses["paper 15"] = {
    "title": "DT-Driven Communication-Efficient Federated Anomaly Detection for IIoT",
    "gaps_text": get_text_from_pages(p15_reader, range(11, min(14, len(p15_reader.pages))))
}

# 7. Paper 3: Urban DTs Review
p3_reader = PdfReader(os.path.join(papers_dir, "paper 3.pdf"))
detailed_analyses["paper 3"] = {
    "title": "A Review of Urban Digital Twins Integration, Challenges, and Future Directions",
    "gaps_text": get_text_from_pages(p3_reader, range(25, min(32, len(p3_reader.pages))))
}

# 8. Paper 12: A New Era for Digital Twins
p12_reader = PdfReader(os.path.join(papers_dir, "paper 12.pdf"))
detailed_analyses["paper 12"] = {
    "title": "A New Era for Digital Twins: Progress and Industry Adoption",
    "gaps_text": get_text_from_pages(p12_reader, range(34, min(42, len(p12_reader.pages))))
}

out_path = os.path.normpath(os.path.join(script_dir, "deep_gaps_extraction.json"))
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(detailed_analyses, f, indent=2, ensure_ascii=False)

print("Deep extraction complete.")
