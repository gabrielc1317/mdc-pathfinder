from fastapi import APIRouter
from ..util.files import load_json

router = APIRouter(prefix="/goals", tags=["goals"])

@router.get("")
def list_goals():
    goals = load_json("career_goals.json")
    return {"goals": goals}
