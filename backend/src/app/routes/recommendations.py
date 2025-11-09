from math import ceil
from pydantic import BaseModel
from fastapi import APIRouter
from ..util.files import load_csv, load_json
from ..services.matcher import score_candidates, boost_by_delivery, remaining_credits
from ..services.cost_estimator import estimate_terms, estimate_cost
from ..services.typing import CostModel
from fastapi import HTTPException
from ..agents.orchestrator import recommend_with_gemini
from ..util.validate import is_valid_program
from ..services.matcher import (
    score_candidates, boost_by_delivery, remaining_credits,
    _goal_prefs, boost_by_goal_prefs
)
from ..util.validate import is_valid_program
router = APIRouter(prefix="/recommendations", tags=["recommendations"])

class RecRequest(BaseModel):
    priorEducation: str           # "hs" | "some_college" | "aa" | "as" | "bs"
    goalId: int
    earnedCredits: int = 0
    preferOnline: bool = False

@router.post("")
def recommend(req: RecRequest):
    programs = load_csv("programs_mdc.csv")
    mappings = load_json("goal_program_map_mdc.json")
    cost_model = CostModel(**load_json("cost_model.json"))
    prefs = _goal_prefs(req.goalId)
    # Filter to real programs (avoid catalog noise)
    programs = [p for p in programs if is_valid_program(p)]

    base_scores = score_candidates(req.goalId, mappings)

    cands = []
    for p in programs:
        try:
            pid = int(p.get("id"))
        except Exception:
            continue
        if pid not in base_scores:
            continue

        try:
            total_cr = int(p.get("total_credits") or 0)
        except Exception:
            total_cr = 0

        score = base_scores[pid]
        score = boost_by_delivery(score, p.get("delivery_mode"), req.preferOnline)
        score = boost_by_goal_prefs(score, p, prefs)

 

        rem = remaining_credits(total_cr, req.earnedCredits)
        terms = estimate_terms(rem)
        cost = estimate_cost(rem, terms, cost_model, pid)

        cands.append({
        "score": score,
        "program": {
            "id": pid,
            "name": p.get("name"),
            "award_level": p.get("award_level"),
            "total_credits": total_cr,
            "url": p.get("url"),
        },
        "remaining_credits": rem,
        "estimated_terms": terms,
        "estimated_cost": cost,
        "why_this": (
            f"Matched goal {req.goalId}; fit_strength={base_scores[pid]}; "
            f"{'online-friendly' if (p.get('delivery_mode') or '').lower() in ('online','hybrid') else 'on-campus'}"
        ),
    })

    # Sort by score desc, then remaining credits asc
    cands.sort(key=lambda x: (-x["score"], x["remaining_credits"]))
    return {"recommendations": cands[:3]}

@router.post("/ai")
def recommend_ai(req: RecRequest):
    try:
        payload = {
            "priorEducation": req.priorEducation,
            "goalId": req.goalId,
            "earnedCredits": req.earnedCredits,
            "preferOnline": req.preferOnline
        }
        return recommend_with_gemini(payload)
    except Exception as e:
        # Hard fallback to heuristic if AI path fails
        return recommend(req)

