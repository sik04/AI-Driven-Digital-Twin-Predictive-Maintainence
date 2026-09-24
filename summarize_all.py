import json
import re

json_path = r"C:\Users\shiks\.gemini\antigravity-ide\brain\3812dc48-8d39-4ddf-afd7-ff43db401eba\scratch\papers_summary.json"
with open(json_path, "r", encoding="utf-8") as f:
    papers = json.load(f)

summary_output = []

for p in papers:
    fname = p.get("filename")
    pages = p.get("num_pages")
    first_text = p.get("first_pages_text", "")
    last_text = p.get("last_pages_text", "")
    sections = p.get("sections_found", {})
    
    # Try to extract title
    lines = [line.strip() for line in first_text.split("\n") if line.strip()]
    
    summary_output.append({
        "file": fname,
        "pages": pages,
        "header_sample": lines[:12],
        "sections": {k: v[:600] for k, v in sections.items()}
    })

out_txt = r"C:\Users\shiks\.gemini\antigravity-ide\brain\3812dc48-8d39-4ddf-afd7-ff43db401eba\scratch\all_papers_overview.txt"
with open(out_txt, "w", encoding="utf-8") as f:
    for item in summary_output:
        f.write("=" * 80 + "\n")
        f.write(f"FILE: {item['file']} ({item['pages']} pages)\n")
        f.write("HEADER LINES:\n")
        for line in item["header_sample"]:
            f.write(f"  {line}\n")
        f.write("\nSECTIONS FOUND:\n")
        for sec, text in item["sections"].items():
            f.write(f"  [{sec.upper()}]:\n    {text.strip()}\n\n")

print(f"Saved overview of all {len(summary_output)} papers to {out_txt}")
