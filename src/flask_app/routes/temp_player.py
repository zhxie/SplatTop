#### THIS FILE IS TEMPORARY JUST TO SERVE DATA TO THE FRONTEND FOR DEVELOPMENT ####
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import text

from flask_app.connections import async_session, celery, connection_manager
from shared_lib.queries.player_queries import PLAYER_ALIAS_QUERY

router = APIRouter()

logger = logging.getLogger(__name__)


@router.get("/player_test/{player_id}")
async def temp_player(player_id: str):
    async with async_session() as session:  # Ensure you have an asynchronous session
        logger.info("Fetching initial player data")
        result = await session.execute(
            text(PLAYER_ALIAS_QUERY), {"player_id": player_id}
        )
        result = result.fetchall()

    logger.info("Initial player data fetched")
    result = [{**row._asdict()} for row in result]
    for player in result:
        player["latest_updated_timestamp"] = player[
            "latest_updated_timestamp"
        ].isoformat()

    logger.info("Returning initial player data")
    return result


@router.websocket("/ws/player/{player_id}")
async def websocket_endpoint(websocket: WebSocket, player_id: str):
    await connection_manager.connect(websocket, player_id)
    try:
        while True:
            data = await websocket.receive_text()
            await connection_manager.send_personal_message(
                f"You wrote: {data}", player_id
            )
    except WebSocketDisconnect:
        connection_manager.disconnect(player_id)
