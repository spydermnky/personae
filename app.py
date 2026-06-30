from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
import engine

app = FastAPI(title="The Locked Room")

game = engine.load_suspects()

class AskRequest(BaseModel):
    suspect: str
    message: str

@app.get("/")
def home():
    return FileResponse("index.html")

@app.get("/api/suspects")
def list_suspects():
    return {"suspects": {key: data["name"] for key, data in game.items()}}

@app.post("/api/ask")
def ask(req: AskRequest):
    if req.suspect not in game:
        return {"error": f"No suspect named '{req.suspect}'."}
    reply = engine.ask(game[req.suspect], req.message)
    return {"reply": reply}
 
@app.post("/api/reset")
def reset():
    global game
    game = engine.load_suspects()
    return {"status": "reset"}