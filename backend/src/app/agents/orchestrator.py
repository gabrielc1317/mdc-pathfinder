import os, json
from typing import Any, Dict, List
from dotenv import load_dotenv
import google.generativeai as genai

from .tools import tool_search_programs, tool_get_program_details, tool_estimate_cost
from ..util.files import load_csv, load_json
from ..services.matcher import remaining_credits
from ..services.cost_estimator import estimate_terms, estimate_cost
from ..services.typing import CostModel

load_dotenv()

def _valid_program_ids() -> set[int]:
    ids = set()
    for p in load_csv("programs_mdc.csv"):
        try: ids.add(int(p["id"]))
        except: pass
    return ids

def _fallback(req: Dict[str, Any]) -> Dict[str, Any]:
    # Use the heuristic path if AI fails
    mappings = load_json("goal_program_map_mdc.json")
    programs = load_csv("programs_mdc.csv")
    base_scores = {}
    for m in mappings:
        if int(m.get("goal_id", -1)) == int(req["goalId"]):
            pid = int(m["program_id"])
            base_scores[pid] = max(base_scores.get(pid, 0), int(m.get("fit_strength", 3)))
    cm = CostModel(**load_json("cost_model.json"))
    cands = []
    for p in programs:
        pid = int(p["id"])
        if pid not in base_scores:
            continue
        total = int(p.get("total_credits") or 0)
        rem = max(0, total - int(req.get("earnedCredits") or 0))
        terms = estimate_terms(rem)
        cost = estimate_cost(rem, terms, cm, pid)
        cands.append({
            "score": base_scores[pid],
            "program": { "id": pid, "name": p.get("name"), "award_level": p.get("award_level"), "url": p.get("url") },
            "remaining_credits": rem,
            "estimated_terms": terms,
            "estimated_cost": cost,
            "why_this": f"Heuristic match (fit_strength={base_scores[pid]})."
        })
    cands.sort(key=lambda x: (-x["score"], x["remaining_credits"]))
    return {
            "recommendations": cands[:3],
            "advising_disclaimer": "Check the official MDC catalog/advisors for the most current requirements.",
            "debug": {"origin": "fallback"}
    }

def recommend_with_gemini(req: Dict[str, Any]) -> Dict[str, Any]:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return _fallback(req)

    genai.configure(api_key=api_key)

    # Load function declarations from JSON files
    base = os.path.join(os.path.dirname(__file__), "schemas")
    f_search = json.load(open(os.path.join(base, "searchPrograms.json"), "r", encoding="utf-8"))
    f_details = json.load(open(os.path.join(base, "getProgramDetails.json"), "r", encoding="utf-8"))
    f_cost = json.load(open(os.path.join(base, "estimateCost.json"), "r", encoding="utf-8"))

    model = genai.GenerativeModel(
        model="gemini-1.5-pro-latest",
        tools=[{"function_declarations":[f_search, f_details, f_cost]}],
        system_instruction=open(os.path.join(os.path.dirname(__file__), "prompts", "system_prompt.txt"), "r", encoding="utf-8").read()
    )

    chat = model.start_chat(history=[])

    # Kick off with user inputs
    resp = chat.send_message(json.dumps({
        "goalId": req["goalId"],
        "priorEducation": req.get("priorEducation","hs"),
        "earnedCredits": int(req.get("earnedCredits",0)),
        "preferOnline": bool(req.get("preferOnline",False))
    }))

    # Handle tool calls
    MAX_STEPS = 6
    for _ in range(MAX_STEPS):
        parts = getattr(resp.candidates[0].content, "parts", []) if resp and resp.candidates else []
        calls = [p.function_call for p in parts if getattr(p, "function_call", None)]
        if not calls:
            break

        for call in calls:
            name = call.name
            args = dict(call.args.items()) if hasattr(call, "args") else {}

            if name == "searchPrograms":
                out = tool_search_programs(
                    goalId=int(args.get("goalId")),
                    priorEducation=args.get("priorEducation"),
                    earnedCredits=int(args.get("earnedCredits",0)),
                    preferOnline=bool(args.get("preferOnline",False))
                )
                resp = chat.send_message(genai.FunctionResponse(name=name, response={"candidates": out}))
            elif name == "getProgramDetails":
                out = tool_get_program_details(int(args.get("program_id")))
                resp = chat.send_message(genai.FunctionResponse(name=name, response={"program": out}))
            elif name == "estimateCost":
                out = tool_estimate_cost(int(args.get("program_id")), int(args.get("remaining_credits",0)))
                resp = chat.send_message(genai.FunctionResponse(name=name, response={"estimate": out}))
            else:
                # Unknown tool; stop tool loop
                break

    # Final answer should be JSON per system prompt
    try:
        data = json.loads(resp.text)
    except Exception:
        return _fallback(req)

    # Validate program IDs and trim to 3
    valid_ids = _valid_program_ids()
    recs = []
    for r in data.get("recommendations", []):
        pid = r.get("program", {}).get("id")
        if isinstance(pid, int) and pid in valid_ids:
            recs.append(r)

    if not recs:
        return _fallback(req)

    return {
            "recommendations": recs[:3],
            "advising_disclaimer": data.get("advising_disclaimer") or "Check the official MDC catalog/advisors for the most current requirements.",
            "debug": {"origin": "ai"}
    }
