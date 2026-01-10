from . import db
from typing import List
import datetime
from sqlalchemy import Integer, String, ForeignKey, JSON, Date, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class UserStat(db.Model):
    __tablename__ = 'users_stat'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    recorded_at: Mapped[datetime.date] = mapped_column(Date(), default=datetime.date.today)

    success: Mapped[List['int']] = mapped_column(JSON)
    failed: Mapped[List['int']] = mapped_column(JSON)
