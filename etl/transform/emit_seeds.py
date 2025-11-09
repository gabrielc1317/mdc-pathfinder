# etl/transform/emit_seeds.py
import json, argparse, csv, re
from pathlib import Path
from collections import defaultdict

GOAL_TAG_MAP = {
    1:  ["cs","software","programming","web","frontend"],  # Software Engineer
    2:  ["animation","game"],                             # Web/Animation Artist (or rename goal later)
    3:  ["ai","ml","vision","nlp"],                      # AI/ML Engineer
    4:  ["architecture"],                                 # Architect
    5:  ["aviation"],                                     # Aviation Maintenance Manager
    6:  ["biomedical"],                                   # Biomedical Equipment Technician
    7:  ["biotech"],                                      # Biotechnology Lab Technician
    8:  ["construction"],                                 # Construction Manager
    9:  ["business"],                                     # Business Administrator
    10: ["data","bi","analytics","sql","viz","reports"],  # Business Intelligence Analyst
    11: ["cybersecurity","security"],                     # Cybersecurity Analyst
    12: ["accounting"],                                   # Accountant
    13: ["agriculture"],                                  # Agricultural Scientist
    14: ["anthropology"],                                 # Anthropologist
    15: ["biology"],                                      # Biologist
    16: ["chemistry"],                                    # Chemist
    17: ["cs","computer science"],                        # Computer Scientist
    18: ["economics"],                                    # Economist
    19: ["civil"],                                        # Civil Engineer
    20: ["electrical"],                                   # Electrical Engineer
    21: ["mechanical"],                                   # Mechanical Engineer
    22: ["biomedical"],                                   # Biomedical Engineer
    23: ["architect"],                                    # Architectural Engineer (adjust tag if needed)
}

def load_goals(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return {g["id"]: g["name"] for g in json.load(f)}

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--programs", required=True, help="data/seed/programs_mdc.csv")
    ap.add_argument("--goals", required=True, help="data/seed/career_goals.json")
    ap.add_argument("--map-out", default="data/seed/goal_program_map_mdc.json")
    args = ap.parse_args(argv)

    goals = load_goals(Path(args.goals))

    # Load programs
    programs = []
    with open(args.programs, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["tags"] = (row.get("tags") or "").lower()
            row["name"] = (row.get("name") or "")
            row["award_level"] = (row.get("award_level") or "")
            programs.append(row)

    # First-pass mapping by tag match
    mappings = []
    for goal_id, goal_name in goals.items():
        tag_list = GOAL_TAG_MAP.get(goal_id, [])
        for p in programs:
            score = 0
            for t in tag_list:
                if t and t in p["tags"]:
                    score += 1
            # small boost: award alignment (AA for transfer-y, AS for applied)
            if goal_id in (1,17,19,20,21,22) and p["award_level"] == "AA":
                score += 1
            if goal_id in (2,6,7,8,9,10,11,12) and p["award_level"] in ("AS","AAS","BAS"):
                score += 1

            if score > 0:
                mappings.append({
                    "goal_id": goal_id,
                    "program_id": int(p["id"]),
                    "fit_strength": min(5, 2 + score),  # default scaling
                    "rationale": f"Tag match for goal '{goal_name}' ({', '.join(tag_list)}) and award alignment."
                })

    # Deduplicate by (goal_id, program_id) keeping highest fit
    best = {}
    for m in mappings:
        k = (m["goal_id"], m["program_id"])
        if k not in best or m["fit_strength"] > best[k]["fit_strength"]:
            best[k] = m

    out = list(best.values())
    Path(args.map_out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.map_out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(out)} mappings → {args.map_out}")

if __name__ == "__main__":
    main()
