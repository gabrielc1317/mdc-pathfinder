from math import ceil
from .typing import CostModel

def estimate_terms(remaining_credits: int, credit_load_per_term: int = 15) -> int:
    if remaining_credits <= 0:
        return 0
    return ceil(remaining_credits / max(1, credit_load_per_term))

def estimate_cost(remaining_credits: int, terms: int, cost_model: CostModel, program_id: int | None):
    # Program override wins if present
    if program_id is not None and str(program_id) in cost_model.program_overrides:
        total = float(cost_model.program_overrides[str(program_id)])
        return {"tuition": total, "fees": 0.0, "books": 0.0, "total": total}

    tuition = cost_model.in_state_per_credit * remaining_credits
    fees = cost_model.tech_fee_per_credit * remaining_credits + cost_model.term_fee_flat * terms
    books = cost_model.book_allowance_per_term * terms
    return {"tuition": round(tuition, 2), "fees": round(fees, 2), "books": round(books, 2),
            "total": round(tuition + fees + books, 2)}
