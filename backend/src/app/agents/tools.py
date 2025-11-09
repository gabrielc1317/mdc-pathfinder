# backend/src/app/agents/tools.py (replace _programs with this)
from typing import Any, Dict, List
from ..util.files import load_csv, load_json
from ..services.matcher import score_candidates, boost_by_delivery, remaining_credits
from ..services.cost_estimator import estimate_terms, estimate_cost
from ..services.typing import CostModel
from ..util.validate import is_valid_program  # <-- NEW
from ..util.files import load_csv, load_json
from ..services.matcher import (
    score_candidates, boost_by_delivery, remaining_credits,
    _goal_prefs, boost_by_goal_prefs
)
from ..services.cost_estimator import estimate_terms, estimate_cost
from ..services.typing import CostModel


VALID_AWARDS = {"AA","AS","AAS","BAS","BS","CERTIFICATE"}

def _programs():
    progs = load_csv("programs_mdc.csv")
    out = []
    for p in progs:
        try:
            p["total_credits"] = int(p.get("total_credits") or 0)
        except Exception:
            p["total_credits"] = 0
        if is_valid_program(p):
            out.append(p)
    return out
def tool_search_programs(goalId: int, priorEducation: str | None, earnedCredits: int | None, preferOnline: bool | None):
    mappings = load_json("goal_program_map_mdc.json")
    progs = _programs()
    scored = score_candidates(goalId, mappings)
    prefs = _goal_prefs(goalId)

    res = []
    for p in progs:
        try:
            pid = int(p["id"])
        except Exception:
            continue
        if pid not in scored:
            continue

        s = scored[pid]
        s = boost_by_delivery(s, p.get("delivery_mode"), bool(preferOnline))
        s = boost_by_goal_prefs(s, p, prefs)
        # optional:
        # s += penalty_generic_title(p.get("name"))

        res.append({
            "program_id": pid,
            "name": p.get("name"),
            "award_level": p.get("award_level"),
            "url": p.get("url") or None,
            "score": s
        })

    res.sort(key=lambda x: -x["score"])
    return res[:6]

def tool_get_program_details(program_id: int):
    for p in _programs():
        if str(p["id"]) == str(program_id):
            return {
                "program_id": int(p["id"]),
                "name": p.get("name"),
                "award_level": p.get("award_level"),
                "total_credits": int(p.get("total_credits") or 0),
                "url": p.get("url") or None,
                "delivery_mode": p.get("delivery_mode"),
                "campuses": p.get("campuses"),
                "tags": p.get("tags"),
                "description": p.get("description")
            }
    return None

def tool_estimate_cost(program_id: int, remaining_credits: int):
    cm = CostModel(**load_json("cost_model.json"))
    terms = estimate_terms(remaining_credits)
    return estimate_cost(remaining_credits, terms, cm, program_id) | {"estimated_terms": terms}
