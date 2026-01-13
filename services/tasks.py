from typing import List
from models import db
from models.user import User
from models.word import Word, WordStatistics
from sqlalchemy import func, and_, nulls_first
from sqlalchemy.orm import joinedload, selectinload


class TaskService:

    @classmethod
    def get_user_spelling_task(cls, user :User, count: int = 20, min_level :int = 0, max_level :int = 10) -> List[Word]:
        words = []
        repeat_count = count // 5

        repeat_query = db.select(Word).options(joinedload(Word.spellings)).join(
            WordStatistics,
            and_(
                Word.id == WordStatistics.word_id,
                WordStatistics.user_id == user.id,
                WordStatistics.failed > 0
            )
        ).filter(
            Word.spellings.any()
        ).filter(
            Word.level >= min_level
        ).filter(
            Word.level <= max_level
        ).order_by(
            func.random()
        ).limit(repeat_count)

        words += db.session.execute(repeat_query).unique().scalars().all()

        query = db.select(Word).options(joinedload(Word.spellings)).outerjoin(
            WordStatistics,
            and_(
                Word.id == WordStatistics.word_id,
                WordStatistics.user_id == user.id
            )
        ).filter(
            Word.spellings.any()
        ).filter(
            Word.level >= min_level
        ).filter(
            Word.level <= max_level
        ).filter(
            Word.id.notin_([word.id for word in words])
        ).order_by(
            nulls_first(WordStatistics.failed+WordStatistics.success), func.random()
        ).limit(
            count - len(words)
        )

        words += db.session.execute(query).unique().scalars()
        return words
