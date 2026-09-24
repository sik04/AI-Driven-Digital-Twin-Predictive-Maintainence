import json

with open(r"C:\Users\shiks\.gemini\antigravity-ide\brain\3812dc48-8d39-4ddf-afd7-ff43db401eba\scratch\extra_papers_deep.json", "r", encoding="utf-8") as f:
    data = json.load(f)

out_summary = r"C:\Users\shiks\.gemini\antigravity-ide\brain\3812dc48-8d39-4ddf-afd7-ff43db401eba\scratch\extra_summary_clean.txt"
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
