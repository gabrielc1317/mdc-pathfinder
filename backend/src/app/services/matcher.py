from typing import Any, Dict, List
from ..util.files import load_json

def _goal_prefs(goal_id: int):
    goals = load_json("career_goals.json")
    for g in goals:
        if int(g.get("id")) == int(goal_id):
            return {
                "preferred_tags": set((g.get("preferred_tags") or [])),
                "preferred_awards": set((g.get("preferred_awards") or []))
            }
    return {"preferred_tags": set(), "preferred_awards": set()}
def score_candidates(goal_id: int, mappings: List[Dict[str, Any]]) -> Dict[int, int]:
    # return {program_id: fit_strength}
    out: Dict[int,int] = {}
    for m in mappings:
        if int(m.get("goal_id", -1)) == int(goal_id):
            pid = int(m["program_id"])
            fit = int(m.get("fit_strength", 3))
            out[pid] = max(out.get(pid, 0), fit)
    return out

def boost_by_goal_prefs(score, program, prefs):
    # award preference
    award = (program.get("award_level") or "").upper()
    if prefs["preferred_awards"]:
        if award in prefs["preferred_awards"]:
            score += 2
        else:
            score -= 2  # nudge down AA if goal prefers AS/BS/BAS

    # tag overlap
    prog_tags = set((program.get("tags") or "").lower().split(";"))
    overlap = prefs["preferred_tags"].intersection(prog_tags)
    score += 2 * len(overlap)
    return score

def boost_by_delivery(base_score: int, delivery_mode: str | None, prefer_online: bool) -> int:
    if not prefer_online: 
        return base_score
    dm = (delivery_mode or "").lower()
    if dm in ("online", "hybrid"):
        return base_score + 1
    return base_score

def remaining_credits(total_credits: int, earned_credits: int) -> int:
    return max(0, int(total_credits or 0) - max(0, int(earned_credits or 0)))
