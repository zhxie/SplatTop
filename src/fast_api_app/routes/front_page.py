import orjson
from fastapi import APIRouter, HTTPException, Query

from fast_api_app.connections import redis_conn
from shared_lib.constants import MODES

router = APIRouter()


@router.get("/api/leaderboard")
async def leaderboard(
    mode: str = Query(
        "Splat Zones", description="Game mode for the leaderboard"
    ),
    region: str = Query("Tentatek", description="Region for the leaderboard"),
):
    region_bool = "Takoroka" if region == "Takoroka" else "Tentatek"

    redis_key = f"leaderboard_data:{mode}:{region_bool}"
    players = redis_conn.get(redis_key)

    if players is None:
        raise HTTPException(
            status_code=503,
            detail="Data is not available yet, please wait.",
        )
    else:
        players: list[dict] = orjson.loads(players)
        out: dict[str, list] = {}
        for player in players:
            for key, value in player.items():
                if key not in out:
                    out[key] = []
                out[key].append(value)
        return {"players": out}
