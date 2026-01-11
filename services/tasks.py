from typing import List
from models import db
from models.user import User
from models.word import Word, Spelling
from sqlalchemy import func
from sqlalchemy.orm import joinedload, selectinload


class TaskService:

    @classmethod
    def get_user_spelling_task(cls, user :User, count: int = 20, min_level :int = 0, max_level :int = 10) -> List[Word]:
        query = db.select(
            Word
        ).options(
            selectinload(Word.spellings)
        ).filter(
            Word.spellings.any()
        ).filter(
            Word.level >= min_level
        ).filter(
            Word.level <= max_level
        ).order_by(
            func.random()
        ).limit(
            count
        )
        return db.session.execute(query).scalars()
