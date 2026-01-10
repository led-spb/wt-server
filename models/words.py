from . import db
from typing import List
from sqlalchemy import Integer, String, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship, query_expression


class Word(db.Model):
    __tablename__ = 'words'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    fullword: Mapped[str] = mapped_column(String(50), nullable=False, name='full_word')
    context: Mapped[str] = mapped_column(String(500), nullable=True)
    description: Mapped[str] = mapped_column(String(1000), nullable=True)
    spellings: Mapped[List["Spelling"]] = relationship(cascade='all,delete')


class Spelling(db.Model):
    __tablename__ = 'spellings'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    word_id: Mapped[int] = mapped_column(ForeignKey("words.id"))
    position: Mapped[int] = mapped_column(nullable=False)
    length: Mapped[int] = mapped_column(nullable=False)
    variants: Mapped[List['str']] = mapped_column(JSON)
