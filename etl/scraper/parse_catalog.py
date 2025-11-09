# etl/scraper/parse_catalog.py
import json, re, sys, argparse, hashlib
from pathlib import Path
from typing import List, Dict, Any
from unidecode import unidecode
import fitz  # PyMuPDF
from tqdm import tqdm

# Heuristics
AWARD_PAT = re.compile(r'\b(Associate in Science|Associate in Arts|Bachelor|BAS|BS|AAS|Certificate)\b', re.I)
CREDITS_PAT = re.compile(r'Program credits:\s*([0-9]{2,3})', re.I)
TUITION_PAT = re.compile(r'Estimated tuition cost:\s*\$?\s*([0-9,]+\.\d{2})', re.I)
TIME_PAT = re.compile(r'Estimated time to complete:\s*([^\n]+)', re.I)
KEY_COURSES_HDR = re.compile(r'(Key courses|Some key courses|Areas of Study|Program areas of study|As part of this program).*', re.I)

def stable_program_id(name: str, award: str) -> int:
    """Deterministic small int from program name + award."""
    base = f"{name}|{award}".lower().strip()
    h = hashlib.md5(base.encode('utf-8')).hexdigest()
    # 5-digit int space to reduce collision risk for demo
    return int(h[:7], 16) % 900000 + 10000

def clean_text(s: str) -> str:
    return re.sub(r'\s+', ' ', unidecode(s)).strip()

def is_likely_program_title(line: str) -> bool:
    # Many MDC program titles contain the award nearby; we also allow strong-cased lines.
    return bool(AWARD_PAT.search(line)) and len(line) <= 140

def extract_blocks(doc) -> List[Dict[str, Any]]:
    """
    Very simple block extractor:
    - Scan sequentially; when we hit a line that looks like a program title, start a new block.
    - Append lines until next title; capture page span.
    """
    blocks = []
    current = None
    for page_index in tqdm(range(len(doc)), desc="Scanning pages"):
        page = doc.load_page(page_index)
        # Order the text lines top→bottom
        lines = [clean_text(b) for b in page.get_text("text").split('\n')]
        for line in lines:
            if not line:
                continue
            if is_likely_program_title(line):
                # Start a new block
                if current:
                    blocks.append(current)
                current = {
                    "title": line,
                    "pages": [page_index + 1],  # 1-based
                    "text": []
                }
            elif current:
                current["text"].append(line)
                if (page_index + 1) not in current["pages"]:
                    current["pages"].append(page_index + 1)

    if current:
        blocks.append(current)
    return blocks

def parse_program_block(block: Dict[str, Any]) -> Dict[str, Any]:
    text = "\n".join(block["text"])
    title = block["title"]

    # Name + award_level
    award_match = AWARD_PAT.search(title) or AWARD_PAT.search(text)
    award_level = award_match.group(1) if award_match else "TBD"

    # Program name: remove trailing award terms if inside title
    name = title
    name = re.sub(r'\s*(Associate in Science|Associate in Arts|Bachelor|BAS|BS|AAS|Certificate)\s*$', '', name, flags=re.I)
    name = clean_text(name)

    # Credits / tuition / time
    total_credits = None
    m = CREDITS_PAT.search(text)
    if m:
        try:
            total_credits = int(m.group(1))
        except ValueError:
            total_credits = None

    tuition_total = None
    mt = TUITION_PAT.search(text)
    if mt:
        tuition_total = float(mt.group(1).replace(',', ''))

    est_time = None
    mtm = TIME_PAT.search(text)
    if mtm:
        est_time = clean_text(mtm.group(1))

    # Overview: first 1–3 paragraphs before "Areas of Study"/"Key courses"
    overview = []
    for line in block["text"]:
        if KEY_COURSES_HDR.search(line):
            break
        if len(line.split()) > 6:
            overview.append(line)
        if len(" ".join(overview)) > 700:
            break
    overview_txt = clean_text(" ".join(overview)) if overview else ""

    # Key courses: lines after the header until blank/next section
    key_courses = []
    after_hdr = False
    for line in block["text"]:
        if KEY_COURSES_HDR.search(line):
            after_hdr = True
            continue
        if after_hdr:
            if not line.strip():
                break
            # Course code pattern e.g., ACG2021 or words in bullets
            if re.search(r'\b[A-Z]{3,4}\d{4}\b', line):
                # Extract all codes on the line
                codes = re.findall(r'\b[A-Z]{3,4}\d{4}\b', line)
                key_courses.extend(codes)
            else:
                # bullet-style list without codes; keep short labels
                if len(line) <= 60:
                    key_courses.append(line.strip())
            # Stop if too many
            if len(key_courses) >= 20:
                break

    award_norm = award_level.upper()
    # Normalize common long forms
    if award_norm == "ASSOCIATE IN SCIENCE": award_norm = "AS"
    if award_norm == "ASSOCIATE IN ARTS": award_norm = "AA"

    pid = stable_program_id(name, award_norm)

    return {
        "program_id": pid,
        "name": name,
        "award_level": award_norm,
        "total_credits": total_credits,
        "estimated_tuition_cost": tuition_total,
        "estimated_time": est_time,
        "overview": overview_txt,
        "key_courses": list(dict.fromkeys(key_courses)),  # dedupe keep order
        "page_spans": block["pages"]
    }

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf_path", help="Path to catalog PDF (e.g., data/raw/mdc_catalog_2025.pdf)")
    ap.add_argument("--out", default="data/exports", help="Output directory")
    args = ap.parse_args(argv)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_jsonl = out_dir / "catalog_programs.jsonl"

    doc = fitz.open(args.pdf_path)
    blocks = extract_blocks(doc)

    count = 0
    with open(out_jsonl, "w", encoding="utf-8") as f:
        for b in tqdm(blocks, desc="Parsing program blocks"):
            try:
                record = parse_program_block(b)
                # basic sanity
                if record["name"] and record["award_level"]:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
                    count += 1
            except Exception as e:
                # Skip malformed blocks but continue
                sys.stderr.write(f"[warn] block skipped: {e}\n")

    print(f"Wrote {count} program records → {out_jsonl}")

if __name__ == "__main__":
    main()
