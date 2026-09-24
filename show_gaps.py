import json

with open(r"C:\Users\shiks\.gemini\antigravity-ide\brain\3812dc48-8d39-4ddf-afd7-ff43db401eba\scratch\deep_gaps_extraction.json", "r", encoding="utf-8") as f:
    data = json.load(f)

out_file = r"C:\Users\shiks\.gemini\antigravity-ide\brain\3812dc48-8d39-4ddf-afd7-ff43db401eba\scratch\extracted_gaps_summary.txt"
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
