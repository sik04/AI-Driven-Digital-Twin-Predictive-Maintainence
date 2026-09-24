import os
import json

script_dir = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(script_dir, "extra_papers_deep.json")
if not os.path.exists(json_path):
    print(f"File not found: {json_path}")
    exit(0)

with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

out_summary = os.path.join(script_dir, "extra_summary_clean.txt")
with open(out_summary, "w", encoding="utf-8") as out:
    for fname, content in data.items():
        out.write("=" * 80 + "\n")
        out.write(f"FILE: {fname} ({content['num_pages']} pages)\n")
        out.write("--- INTRO / ABSTRACT ---\n")
        for line in content["abstract_intro"].split("\n")[:25]:
            if line.strip():
                out.write(f"  {line.strip()}\n")
        out.write("--- CONCLUSION / FUTURE WORK ---\n")
        for line in content["conclusion_future"].split("\n")[:35]:
            if line.strip():
                out.write(f"  {line.strip()}\n")

print("Saved clean summary.")
