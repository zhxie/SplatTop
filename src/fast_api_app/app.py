import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from fast_api_app.background_tasks import background_runner
from fast_api_app.connections import celery, limiter
from fast_api_app.pubsub import start_pubsub_listener
from fast_api_app.routes import (
    front_page_router,
    infer_router,
    player_detail_router,
    search_router,
    weapon_info_router,
    weapon_leaderboard_router,
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
    celery.send_task("tasks.update_skill_offset")
    celery.send_task("tasks.update_lorenz_and_gini")
    celery.send_task("tasks.fetch_weapon_leaderboard")
    celery.send_task("tasks.fetch_season_results")

    start_pubsub_listener()
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
app.include_router(weapon_leaderboard_router)
app.include_router(infer_router)


# Base route that lists all available routes
@app.get("/api", response_class=HTMLResponse)
async def list_routes():
    html = "<h1>API Endpoints</h1><ul>"
    exclude_paths = [
        "/api/player/",
        "/ws/",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/api/search/",
    ]
    exclude_exact = ["/api"]
    for route in app.routes:
        if (
            hasattr(route, "path")
            and not any(
                route.path.startswith(exclude) for exclude in exclude_paths
            )
            and route.path not in exclude_exact
        ):
            html += f'<li><a href="{route.path}">{route.path}</a></li>'
    html += "</ul>"
    return HTMLResponse(content=html)


# Run the app using Uvicorn programmatically
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")
