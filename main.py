from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from player_service import PlayerService

class PlayerCreate(BaseModel):
    name: str

app = FastAPI(title="Game Player Service")

service = PlayerService({
    "Alice": 120,
    "Bob": 90
})


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/players/{name}")
def get_player(name: str):
    score = service.get_score(name)

    if score is None:
        raise HTTPException(
            status_code=404,
            detail="Player not found"
        )

    return {
        "name": name,
        "score": score
    }

@app.get("/ranking")
def get_ranking():
    ranking = service.get_ranking()

    return {
        "ranking": ranking
    }


@app.post("/players", status_code=201)
def create_player(player: PlayerCreate):
    success = service.add_player(player.name)

    if not success:
        raise HTTPException(
            status_code=400,
            detail="Invalid or duplicate player"
        )

    name = player.name.strip()

    return {
        "name": name,
        "score": service.get_score(name)
    }
