from flask.cli import AppGroup


database_commands = AppGroup('database', help='Manage application database.')


@database_commands.command('create', help='Create database objects')
def create_database():
    from ..models import db
    db.create_all()
