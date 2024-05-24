import logging

from celery import Celery

from celery_app.connections import Session, redis_conn
from celery_app.tasks.front_page import pull_data
from celery_app.tasks.misc import pull_aliases, update_weapon_info
from celery_app.tasks.player_detail import fetch_player_data
from shared_lib.constants import REDIS_URI

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(filename)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

celery = Celery("tasks", broker=REDIS_URI, backend=REDIS_URI)

celery.task(name="tasks.pull_data")(pull_data)
celery.task(name="tasks.fetch_player_data")(fetch_player_data)
celery.task(name="tasks.update_weapon_info")(update_weapon_info)
celery.task(name="tasks.pull_aliases")(pull_aliases)