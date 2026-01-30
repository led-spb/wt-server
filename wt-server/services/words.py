from ..models import db
from ..models.word import Word, Tag, Rule
from sqlalchemy import func
from flask_sqlalchemy.pagination import Pagination

class WordService:

    @classmethod
    def get_by_id(cls, word_id :int) -> Word | None:
        return db.session.execute(
            db.select(Word).filter(Word.id == word_id)
        ).scalar_one_or_none()

    @classmethod
    def find_by_name(cls, word_name: str, context :str = None) -> Word | None:
        query = db.select(
            Word
        ).filter(
            Word.fullword == word_name,
        )
        if context is not None:
            query.filter(Word.context == context)
        return db.session.execute(query).scalar_one_or_none()

    @classmethod
    def get_total_words_count(cls) -> int:
        total_words, = db.session.execute(
            db.select(func.count(Word.id))
        ).one_or_none()

        return total_words

    @classmethod
    def get_tags_dictonary(cls) -> list[Tag]:
        tags = db.session.execute(
            db.select(Tag).order_by(Tag.desciption)
        ).scalars().all()

        return tags

    @classmethod
    def get_rule_by_id(cls, rule_id: int) -> Rule | None:
        return db.session.execute(
            db.select(Rule).filter(Rule.id == rule_id)
        ).scalar_one_or_none()

    @classmethod
    def search_rules(cls, title :str = None, page :int = 1, limit :int = 10) -> Pagination: 
        return db.paginate(
            db.select(
                Rule
            ).filter(
                title is None or func.lower(Rule.title).like(f'%{title}%') 
            ).order_by(Rule.id), page=page, max_per_page=limit
        )
