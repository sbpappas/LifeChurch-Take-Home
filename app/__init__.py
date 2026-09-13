from typing import Optional

from flask import Flask

from app.cache import SimpleCache
from app.config import Config
from app.errors import register_error_handlers
from app.routes import votd_bp
from app.youversion_client import YouVersionClient

def create_app(client: Optional[YouVersionClient] = None, config: Optional[Config] = None) -> Flask:
    app = Flask(__name__)

    if client is None:
        cfg = config or Config() #calls the __init__ in config.py to read env cars
        cache = SimpleCache()
        client = YouVersionClient(cfg, cache)

    app.extensions["youversion_client"] = client #shared gloval state of the app, so we can access app in routes.py

    register_error_handlers(app) # calls errors.py
    app.register_blueprint(votd_bp) # a flask method that merges the routes into the app

    return app
