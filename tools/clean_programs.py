# tools/clean_programs.py
import csv, os, sys
from pathlib import Path

# Resolve repo root -> add backend/src to sys.path no matter where it's run from
HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[1]           # .../mdc-pathways
BACKEND_SRC = REPO_ROOT / "backend" / "src"
sys.path.insert(0, str(BACKEND_SRC))

try:
    from app.util.validate import is_valid_program
except Exception as e:
    print("ERROR: could not import app.util.validate.is_valid_program")
    print("Using sys.path[0:3] =", sys.path[:3])
    raise

SRC = REPO_ROOT / "data" / "seed" / "programs_mdc.csv"
TMP = REPO_ROOT / "data" / "seed" / "_programs_clean.tmp"

def main():
    if not SRC.exists():
        raise FileNotFoundError(f"Missing CSV: {SRC}")

    with open(SRC, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    keep = [r for r in rows if is_valid_program(r)]

    with open(TMP, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(keep)

    os.replace(TMP, SRC)
    print(f"kept_rows {len(keep)} of {len(rows)}")

if __name__ == "__main__":
    main()
