import os
import glob
import json
from pypdf import PdfReader

script_dir = os.path.dirname(os.path.abspath(__file__))
papers_dir = os.path.normpath(os.path.join(script_dir, "..", "papers"))
pdf_files = sorted(glob.glob(os.path.join(papers_dir, "*.pdf")))

results = []

for pdf_path in pdf_files:
    fname = os.path.basename(pdf_path)
    print(f"Processing {fname}...")
    try:
        reader = PdfReader(pdf_path)
        num_pages = len(reader.pages)
        
        # First page or two
        first_pages_text = ""
        for i in range(min(2, num_pages)):
            t = reader.pages[i].extract_text() or ""
            first_pages_text += f"\n--- Page {i+1} ---\n" + t
            
        # Last pages (conclusion, discussion, future work)
        last_pages_text = ""
        start_last = max(0, num_pages - 3)
        for i in range(start_last, num_pages):
            t = reader.pages[i].extract_text() or ""
            last_pages_text += f"\n--- Page {i+1} ---\n" + t
            
        # Full text search for key sections
        full_text = ""
        sections_found = {}
        for i, page in enumerate(reader.pages):
            t = page.extract_text() or ""
            full_text += f"\n--- Page {i+1} ---\n" + t
            t_lower = t.lower()
            for keyword in ["future work", "limitation", "open challenge", "conclusion", "discussion"]:
                if keyword in t_lower and keyword not in sections_found:
                    # extract surrounding snippet
                    idx = t_lower.find(keyword)
                    snippet = t[max(0, idx - 100):min(len(t), idx + 800)]
                    sections_found[keyword] = f"(Page {i+1}): {snippet}"

        results.append({
            "filename": fname,
            "num_pages": num_pages,
            "first_pages_text": first_pages_text[:3000],
            "last_pages_text": last_pages_text[:3000],
            "sections_found": sections_found,
            "full_text_length": len(full_text)
        })
    except Exception as e:
        results.append({
            "filename": fname,
            "error": str(e)
        })

output_path = os.path.normpath(os.path.join(script_dir, "papers_summary.json"))
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"Done. Processed {len(results)} papers. Saved to {output_path}")
