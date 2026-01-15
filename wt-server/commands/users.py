import click
from flask import current_app
from flask.cli import AppGroup
from ..models import db
from ..models.user import User
from ..services.users import UserService


user_commands = AppGroup('user', help='Manage application users.')


@user_commands.command('create', help='Register new user')
@click.argument('name', default=None)
def create_user(name=None):
    if name is None:
        name = click.prompt('username')
    password = click.prompt('password', hide_input=True, confirmation_prompt=True)

    if UserService.get_user_by_login(name):
        raise RuntimeError('User is already exists')

    user = User(name=name)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

@user_commands.command('password', help='Change user password')
@click.argument('name', default=None)
def reset_password(name=None):
    if name is None:
        name = click.prompt('username')
    password = click.prompt('password', hide_input=True, confirmation_prompt=True)

    user = UserService.get_user_by_login(name)
    if user is None:
        raise RuntimeError('User is not found')
    user.set_password(password)

    db.session.add(user)
    db.session.commit()
