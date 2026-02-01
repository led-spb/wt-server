import click
from flask.cli import AppGroup
from ..models import db
from ..models.user import Invite
from ..services.users import UserService
import secrets
import hashlib
from datetime import datetime, timedelta

user_commands = AppGroup('user', help='Manage application users.')


@user_commands.command('create', help='Register new user')
@click.argument('name', default=None)
def create_user(name=None):
    if name is None:
        name = click.prompt('username')
    password = click.prompt('password', hide_input=True, confirmation_prompt=True)

    if UserService.get_user_by_login(name):
        raise RuntimeError('User is already exists')
    UserService.register_user(name, password, None)


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

@user_commands.command('invite', help='Create new invite')
@click.option('--lifetime', type=click.INT, default=14)
def create_invite(lifetime: int):
    hash = hashlib.sha256(secrets.token_bytes(16))
    invite = Invite(
        hash=hash.hexdigest(),
        lifetime=datetime.now() + timedelta(days=lifetime)
    )
    db.session.add(invite)
    db.session.commit()
    pass
