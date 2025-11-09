# etl/transform/normalize_courses.py
import json, sys, argparse
from pathlib import Path
import pandas as pd
import re

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("jsonl_path", help="catalog_courses.jsonl")
    ap.add_argument("--out", default="data/exports/courses.csv")
    args = ap.parse_args(argv)

    rows = []
    try:
        with open(args.jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line)
                code = rec.get("course_code")
                if not code: 
                    # try to infer from title line
                    m = re.search(r'\b([A-Z]{3,4}\d{4})\b', rec.get("title",""))
                    code = m.group(1) if m else None
                if not code: 
                    continue
                rows.append({
                    "course_code": code,
                    "title": rec.get("title",""),
                    "credits": rec.get("credits",""),
                    "description": rec.get("description",""),
                    "prereq": rec.get("prereq",""),
                    "coreq": rec.get("coreq","")
                })
    except FileNotFoundError:
        print(f"[warn] {args.jsonl_path} not found; skipping")
        return

    df = pd.DataFrame(rows).drop_duplicates(subset=["course_code","title"])
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    print(f"Wrote {len(df)} rows → {args.out}")

if __name__ == "__main__":
    main()
