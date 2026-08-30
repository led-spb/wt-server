from . import Base
import datetime
from sqlalchemy import Integer, ForeignKey, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .word import Tag, Rule


class UserStat(Base):
    __tablename__ = 'users_stat'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    recorded_at: Mapped[datetime.date] = mapped_column(Date(), default=datetime.date.today)

    success: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class UserAggregatedStat(Base):
    __tablename__ = 'aggregate_stat'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    recorded_at: Mapped[datetime.date] = mapped_column(Date(), nullable=False, default=datetime.date.today)

    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id"), nullable=True)
    rule_id: Mapped[int] = mapped_column(ForeignKey("rules.id"), nullable=True)
    total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    tag: Mapped[Tag] = relationship()
    rule: Mapped[Rule] = relationship()
