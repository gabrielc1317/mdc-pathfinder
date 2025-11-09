# main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
from dotenv import load_dotenv

load_dotenv()  # load .env file if it exists

app = FastAPI()

# Allow your frontend origin (Vite default port)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_API_KEY = os.getenv("VITE_GEMINI_API_KEY")

@app.post("/api/invoke_llm")
async def invoke_llm(request: Request):
    body = await request.json()
    prompt = body.get("prompt")
    response_schema = body.get("response_json_schema")

    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
    }

    if response_schema:
        payload["response_schema"] = response_schema

    gemini_url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-1.5-flash-latest:generateContent?key={GEMINI_API_KEY}"
    )

    r = requests.post(gemini_url, json=payload, headers={"Content-Type": "application/json"})

    if r.status_code != 200:
        return {"error": r.text}

    data = r.json()
    output = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")

    return {"output": output}
