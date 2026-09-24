import json

json_path = r"C:\Users\shiks\.gemini\antigravity-ide\brain\3812dc48-8d39-4ddf-afd7-ff43db401eba\scratch\papers_summary.json"
with open(json_path, "r", encoding="utf-8") as f:
    papers = json.load(f)

for p in papers:
    print("=" * 80)
    print(f"FILE: {p.get('filename')} (Pages: {p.get('num_pages')})")
    first_p = p.get("first_pages_text", "")
    lines = [line.strip() for line in first_p.split("\n") if line.strip()]
    print("--- START OF PAPER ---")
    for l in lines[:15]:
        print("  ", l)
    print("--- EXTRACTED SECTIONS KEYS ---")
    print("  Keys:", list(p.get("sections_found", {}).keys()))
