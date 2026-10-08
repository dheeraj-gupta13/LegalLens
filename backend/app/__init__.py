import os

from dotenv import load_dotenv
from flask import Flask

load_dotenv()

from .config import Config
from .errors import register_error_handlers
from .extensions import cors, db, jwt, limiter


def create_app(config=Config):
    app = Flask(__name__)
    app.config.from_object(config)
    os.makedirs(app.config["UPLOAD_DIR"], exist_ok=True)

    db.init_app(app)
    jwt.init_app(app)
    limiter.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
                  expose_headers=["Location"])
    register_error_handlers(app, jwt)

    from .api import api_v1
    app.register_blueprint(api_v1, url_prefix="/api/v1")

    with app.app_context():
        db.create_all()  # use Flask-Migrate/Alembic for schema changes in production
    return app
