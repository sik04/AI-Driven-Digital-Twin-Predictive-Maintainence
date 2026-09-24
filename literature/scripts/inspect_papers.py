import os

script_dir = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(script_dir, "papers_summary.json")
if not os.path.exists(json_path):
    print(f"Summary file not found at {json_path}. Run extract_papers.py first.")
    exit(0)

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
