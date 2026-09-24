import os
import json

script_dir = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(script_dir, "deep_gaps_extraction.json")
if not os.path.exists(json_path):
    print(f"File not found: {json_path}. Run deep_extract.py first.")
    exit(0)

with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

out_file = os.path.join(script_dir, "extracted_gaps_summary.txt")
with open(out_file, "w", encoding="utf-8") as out:
    for key, val in data.items():
        out.write("=" * 80 + "\n")
        out.write(f"[{key.upper()}] : {val['title']}\n")
        out.write("-" * 80 + "\n")
        text = val["gaps_text"]
        lines = text.split("\n")
        cleaned = [l.strip() for l in lines if l.strip()]
        out.write("\n".join(cleaned) + "\n\n")

print(f"Written gaps summary to {out_file}")
