import flask
from .users import user_commands
from .database import database_commands
from .tools import tools_commands
from .imports import imports_commands


def create_commands(app :flask.Flask):
    app.cli.add_command(user_commands)
    app.cli.add_command(database_commands)
    app.cli.add_command(tools_commands)
    app.cli.add_command(imports_commands)
