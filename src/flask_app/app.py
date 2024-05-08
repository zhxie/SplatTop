import asyncio
import logging
import os
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from flask_app.background_tasks import background_runner
from flask_app.connections import celery, limiter, redis_conn
from flask_app.pubsub import listen_for_updates
from flask_app.routes import (
    front_page_router,
    player_detail_router,
    search_router,
    weapon_info_router,
)

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(filename)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    celery.send_task("tasks.pull_data")
    celery.send_task("tasks.update_weapon_info")
    celery.send_task("tasks.pull_aliases")

    # Start the pubsub listener in a separate daemon thread
    pubsub_thread = threading.Thread(
        target=asyncio.run, args=(listen_for_updates(),), daemon=True
    )
    pubsub_thread.start()
    asyncio.create_task(background_runner.run())
    yield


app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Setup CORS
if os.getenv("ENV") == "development":
    origins = ["http://localhost:3000"]
else:
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(front_page_router)
app.include_router(player_detail_router)
app.include_router(search_router)
app.include_router(weapon_info_router)

# Run the app using Uvicorn programmatically
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")
