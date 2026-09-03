from . import Base
import datetime
from sqlalchemy import Integer, ForeignKey, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .word import Topic, Word

class WordStatistics(Base):
    __tablename__ = 'word_statistics'

    word_id: Mapped[int] = mapped_column(ForeignKey("words.id"), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)

    success: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    word: Mapped[Word] = relationship()


class UserStatistics(Base):
    __tablename__ = 'user_statistics'

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    recorded_at: Mapped[datetime.date] = mapped_column(Date(), default=datetime.date.today, primary_key=True)

    success: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class UserTopicStatistics(Base):
    __tablename__ = 'user_topic_statistics'

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, primary_key=True)
    recorded_at: Mapped[datetime.date] = mapped_column(Date(), nullable=False, primary_key=True, default=datetime.date.today)
    topic_id: Mapped[int] = mapped_column(ForeignKey("tags.id"), nullable=False, primary_key=True)

    success: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    topic: Mapped[Topic] = relationship()
