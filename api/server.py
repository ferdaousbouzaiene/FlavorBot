from fastapi import FastAPI
from pydantic import BaseModel
from src.agents.flavorbot import run_flavorbot

app = FastAPI(title="FlavorBot API")

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
def chat(request: ChatRequest):
    try:
        response = run_flavorbot(request.message)
        return {"response": response}
    except Exception as e:
        return {"error": str(e)}
