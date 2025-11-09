from fastapi import APIRouter, HTTPException, Query
from ..util.files import load_csv

router = APIRouter(prefix="/programs", tags=["programs"])

def _all_programs():
    return load_csv("programs_mdc.csv")

@router.get("")
def list_programs(ids: str | None = Query(default=None, description="comma-separated ids")):
    progs = _all_programs()
    if not ids:
        return {"programs": progs}
    want = {x.strip() for x in ids.split(",")}
    return {"programs": [p for p in progs if str(p.get("id")) in want]}

@router.get("/{program_id}")
def get_program(program_id: int):
    progs = _all_programs()
    for p in progs:
        if str(p.get("id")) == str(program_id):
            return {"program": p}
    raise HTTPException(status_code=404, detail="Program not found")
