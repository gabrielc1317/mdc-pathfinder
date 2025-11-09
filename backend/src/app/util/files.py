from pathlib import Path
import json, csv

# Resolve repo root from backend/src/app/util/files.py
# files.py -> util (0), app (1), src (2), backend (3), mdc-pathways (4)
ROOT = Path(__file__).resolve().parents[4]

def seed_path(*parts) -> Path:
    return ROOT.joinpath("data", "seed", *parts)

def load_json(name: str):
    p = seed_path(name)
    if not p.exists():
        raise FileNotFoundError(f"Seed file not found: {p}")
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def load_csv(name: str):
    p = seed_path(name)
    if not p.exists():
        raise FileNotFoundError(f"Seed file not found: {p}")
    rows = []
    with open(p, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows
