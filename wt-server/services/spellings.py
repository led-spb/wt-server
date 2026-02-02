from ..models import db
from ..models.user import User
from ..models.word import Word, WordStatistics
from sqlalchemy import and_
from sqlalchemy.orm import joinedload


class SpellingService:

    @classmethod
    def find_by_word(cls, word: str, context :str = None) -> list[Word]:
        query = db.select(
            Word
        ).options(
            joinedload(Word.spellings)
        ).filter(
            Word.spellings.any()
        ).filter(
            Word.fullword == word.lower(),
            context is None or Word.context == context,
        )
        return db.session.execute(query).scalars().all()

    @classmethod
    def get_with_user_stats(cls, user: User, filters: list, order_by: list, count: int) -> list[Word]:
        query = db.select(Word).options(
            joinedload(Word.spellings)
        ).outerjoin(
            WordStatistics,
            and_(
                WordStatistics.word_id == Word.id,
                WordStatistics.user_id == user.id
            )
        ).filter(
            Word.spellings.any()
        ).filter(
            *filters
        ).order_by(
            *order_by
        ).limit(
            count
        )
        return db.session.execute(query).unique().scalars().all()
