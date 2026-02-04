from . import db
import datetime
from sqlalchemy import Integer, String, ForeignKey, Date, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    login: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    daily_goal: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    reports: Mapped['UserReport'] = relationship()


class UserStat(db.Model):
    __tablename__ = 'users_stat'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    recorded_at: Mapped[datetime.date] = mapped_column(Date(), default=datetime.date.today)

    success: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class Invite(db.Model):
    __tablename__ = 'invites'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    lifetime: Mapped[datetime.datetime] = mapped_column(DateTime(), nullable=False)
    registered_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)

    registered_user: Mapped[User] = relationship()


class UserReport(db.Model):
    __tablename__ = 'user_reports'

    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), primary_key=True)
    reports: Mapped[list['int']] = mapped_column(JSONB, nullable=True)


class WebPushSubscription(db.Model):
    __tablename__ = 'web_pushes'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    endpoint: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    push_info: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(), nullable=False, default=datetime.datetime.now())

    user: Mapped[User] = relationship()
