from flask import Flask, render_template

from .database import init_db
from .routes import api


def create_app(test_config=None):
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.from_mapping(DATABASE="product_triage.db", TESTING=False)

    if test_config:
        app.config.update(test_config)

    init_db(app)
    app.register_blueprint(api, url_prefix="/api")

    @app.get("/")
    def index():
        return render_template("index.html")

    return app
