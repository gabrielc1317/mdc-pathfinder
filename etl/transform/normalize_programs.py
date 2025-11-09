import json, sys, argparse, re, hashlib
from pathlib import Path
import pandas as pd
from unidecode import unidecode

STOP_PHRASES = re.compile(
    r"(prior to the award|prior to receipt|students entering a florida college system|"
    r"general education|graduation requirements|admission requirements|academic policies|"
    r"rights? and responsibilities|tuition and fees|financial aid)", re.I
)

def guess_award(name: str, award_level: str | None) -> str:
    s = f"{name} {award_level or ''}".lower()
    if "associate in science" in s or re.search(r"\bA\.?S\.?\b", s, re.I): return "AS"
    if "associate in arts"   in s or re.search(r"\bA\.?A\.?\b", s, re.I): return "AA"
    if "bachelor of applied" in s or "bas" in s: return "BAS"
    if re.search(r"\bbachelor\b|\bB\.?S\.?\b|\bB\.?A\.?\b", s, re.I): return "BS"
    if "certificate" in s: return "CERTIFICATE"
    return (award_level or "TBD").upper()

def default_credits_for_award(award: str) -> int:
    if award in {"AA","AS"}: return 60
    if award in {"BAS","BS"}: return 120
    if award == "CERTIFICATE": return 18
    return 0

def clean_text(s: str) -> str:
    return re.sub(r"\s+", " ", unidecode(s or "")).strip()

def looks_like_program_title(name: str) -> bool:
    if not name: return False
    n = name.strip()
    if len(n) < 6 or len(n) > 120: return False
    if STOP_PHRASES.search(n): return False
    # require at least one word >= 3 letters
    return bool(re.search(r"[A-Za-z]{3,}", n))

def guess_tags(name: str, overview: str) -> str:
    txt = f"{name} {overview}".lower()
    tags = set()
    pairs = [
        (r'cyber|security', 'cybersecurity'),
        (r'account', 'accounting'),
        (r'biolog|biotech', 'biotech'),
        (r'chem', 'chemistry'),
        (r'animat|game', 'animation'),
        (r'archit', 'architecture'),
        (r'construc', 'construction'),
        (r'engineer', 'engineering'),
        (r'data|analytics|sql|bi', 'data'),
        (r'computer science|cs', 'cs'),
        (r'ai|machine learning|nlp|vision', 'ai'),
        (r'network', 'network'),
        (r'business', 'business'),
        (r'nurs', 'nursing'),
        (r'aviation', 'aviation')
    ]
    for pat, tg in pairs:
        if re.search(pat, txt): tags.add(tg)
    return ";".join(sorted(tags)) if tags else ""

def stable_program_id(name: str, award: str) -> int:
    base = f"{name}|{award}".lower().strip()
    h = hashlib.md5(base.encode("utf-8")).hexdigest()
    return int(h[:7], 16) % 900000 + 10000

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("jsonl_path", help="data/exports/catalog_programs.jsonl")
    ap.add_argument("--out", default="data/seed/programs_mdc.csv")
    args = ap.parse_args(argv)

    rows = []
    kept = 0
    dropped = 0

    with open(args.jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            name = clean_text(rec.get("name", ""))
            if not looks_like_program_title(name):
                dropped += 1
                continue

            award_raw = rec.get("award_level")
            award = guess_award(name, award_raw)

            # normalize credits with defaults if missing/zero
            total_credits = rec.get("total_credits")
            try:
                cr = int(total_credits) if total_credits is not None else 0
            except Exception:
                cr = 0
            if cr <= 0:
                cr = default_credits_for_award(award)

            overview = clean_text(rec.get("overview", ""))

            # keep only known awards to avoid policy blurbs
            if award not in {"AA","AS","AAS","BAS","BS","CERTIFICATE"}:
                dropped += 1
                continue

            pid = rec.get("program_id")
            if not isinstance(pid, int):
                pid = stable_program_id(name, award)

            rows.append({
                "id": pid,
                "name": name,
                "award_level": award,
                "total_credits": cr,
                "delivery_mode": "TBD",
                "campuses": "TBD",
                "url": "TBD",
                "tags": guess_tags(name, overview),
                "description": overview[:500]
            })
            kept += 1

    df = pd.DataFrame(rows, columns=[
        "id","name","award_level","total_credits","delivery_mode","campuses","url","tags","description"
    ]).drop_duplicates(subset=["id"])

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    print(f"Wrote {len(df)} rows → {args.out} (kept={kept}, dropped={dropped})")

if __name__ == "__main__":
    main()
