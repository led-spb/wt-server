from typing import List, Union
from ..models import db
from ..models.user import User
from ..models.word import Word, WordStatistics, Accent
from sqlalchemy import func, and_, nulls_first
from sqlalchemy.orm import joinedload, selectinload


class AccentService:

    @classmethod
    def find_by_word(cls, word: str) -> List[Word]:
        query = db.select(
            Word
        ).options(
            joinedload(Word.accents)
        ).filter(
            Word.accents.any()
        ).filter(
            Word.fullword == word.lower()
        )
        return db.session.execute(query).scalars().all()


    @classmethod
    def get_with_user_stats(cls, user: User, filters: List, order_by: List, count: int) -> List[Word]:
        query = db.select(Word).options(
            joinedload(Word.accents)
        ).outerjoin(
            WordStatistics
        ).filter(
            WordStatistics.user_id == user.id
        ).filter(
            Word.accents.any()
        ).filter(
            *filters
        ).order_by(
            *order_by
        ).limit(
            count
        )
        return db.session.execute(query).unique().scalars().all()
