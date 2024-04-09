import os

from celery import Celery
from flask import Flask
from flask_caching import Cache
from flask_cors import CORS

from flask_app.celery_tasks import celery  # Import celery instance
from flask_app.database import Session  # Not used, necessary for Session setup
from flask_app.routes import create_front_page_bp, create_player_detail_bp
from flask_app.routes.temp_player import create_temp_player_bp

app = Flask(__name__)

if os.getenv("ENV") == "development":
    CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})
elif os.getenv("ENV") == "production":
    CORS(app)

cache = Cache(app, config={"CACHE_TYPE": "simple"})

front_page_bp = create_front_page_bp()
app.register_blueprint(front_page_bp)

player_detail_bp = create_player_detail_bp()
app.register_blueprint(player_detail_bp)

temp_player_bp = create_temp_player_bp()
app.register_blueprint(temp_player_bp)

celery.send_task("tasks.pull_data")


def run_dev():
    from werkzeug.middleware.profiler import ProfilerMiddleware

    app.config["PROFILE"] = True
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[30])
    app.run(host="0.0.0.0", port=5000, debug=True)


# Removed the if __name__ == "__main__" check as it's not used with gunicorn
