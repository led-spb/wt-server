from flask import Flask

def create_app(config_filename='config.py'):
    app = Flask(__name__)

    app.config.from_pyfile(config_filename)

    from .models import db
    db.init_app(app)

    from .api import create_api
    from .commands import create_commands

    create_api(app)
    create_commands(app)

    return app
