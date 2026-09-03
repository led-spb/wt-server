from enum import Enum
from . import Base
from typing import List
from sqlalchemy import Integer, String, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Word(Base):
    __tablename__ = 'words'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    fullword: Mapped[str] = mapped_column(String(50), nullable=False, name='full_word')
    context: Mapped[str] = mapped_column(String(500), nullable=True)
    tags: Mapped[List['int']] = mapped_column(JSONB, nullable=True)
    rules: Mapped[List['int']] = mapped_column(JSONB, nullable=True)

    spellings: Mapped[List['Spelling']] = relationship(cascade='all,delete')
    accents: Mapped[List['Accent']] = relationship(cascade='all,delete')


class Spelling(Base):
    __tablename__ = 'spellings'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    word_id: Mapped[int] = mapped_column(ForeignKey("words.id"))
    position: Mapped[int] = mapped_column(nullable=False)
    length: Mapped[int] = mapped_column(nullable=False)
    variants: Mapped[List['str']] = mapped_column(JSON)


class Accent(Base):
    __tablename__ = 'accents'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    word_id: Mapped[int] = mapped_column(ForeignKey("words.id"))
    position: Mapped[int] = mapped_column(nullable=False)


class TaskTypeEnum(Enum):
    spelling = 'spelling'
    accent = 'accent'

class Topic(Base):
    __tablename__ = 'tags'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    parent_id: Mapped[int] = mapped_column(Integer, nullable=True)
    description: Mapped[str] = mapped_column(String(250), nullable=False)
    type: Mapped[TaskTypeEnum] = mapped_column(String(20), nullable=False)


class Rule(Base):
    __tablename__ = 'rules'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[TaskTypeEnum] = mapped_column(String(20), nullable=False)
