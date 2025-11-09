from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes.goals import router as goals_router
from .routes.programs import router as programs_router
from .routes.recommendations import router as recs_router
from dotenv import load_dotenv
load_dotenv()
app = FastAPI(title="MDC Pathways API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(goals_router)
app.include_router(programs_router)
app.include_router(recs_router)
