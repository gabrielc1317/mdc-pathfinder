from pydantic import BaseModel
from typing import Dict

class CostModel(BaseModel):
    institution: str
    in_state_per_credit: float
    out_state_per_credit: float
    tech_fee_per_credit: float
    term_fee_flat: float
    book_allowance_per_term: float
    assumptions_note: str | None = None
    program_overrides: Dict[str, float] = {}
