from ..models import db
from ..models.user import User
from ..models.stats import UserStat, UserAggregatedStat
from ..models.word import WordStatistics, Word, Tag
from datetime import date, timedelta
from sqlalchemy import func, case, cast, Numeric, desc, and_, nulls_last, Row
from sqlalchemy.orm import joinedload
from typing import Sequence, Tuple

class UserStatService:

    @classmethod
    def get_user_word_failed(cls, user: User, count :int):
        query = db.select(
            WordStatistics
        ).options(
            joinedload(WordStatistics.word)
        ).filter(
            WordStatistics.user_id == user.id
        ).filter(
            WordStatistics.failed > 0
        ).order_by(
            cast(WordStatistics.success, Numeric) / (WordStatistics.success + WordStatistics.failed)
        ).order_by(
            desc(WordStatistics.failed)
        ).limit(count)

        return db.session.execute(query).scalars()
    
    @classmethod
    def get_user_words_statistics(cls, user: User):
        query = db.select(
            WordStatistics
        ).options(
            joinedload(WordStatistics.word)
        ).filter(
            WordStatistics.user_id == user.id
        )
        return db.session.execute(query).scalars()

    @classmethod
    def get_user_stats(cls, user: User, days :int|None = None):
        query = db.select(UserStat
        ).filter(
            UserStat.user_id == user.id
        ).filter(
            days is None or (UserStat.recorded_at >= date.today() - timedelta(days=days))
        ).order_by(
            UserStat.recorded_at.desc()
        )
        return db.session.execute(query).scalars()


    @classmethod
    def update_user_stat(cls, user: User, success_words: list[int]|None, failed_words: list[int]|None) -> None:
        success = success_words or []
        failed = failed_words or []

        word_stats = db.session.execute(
            db.select(
                Word, WordStatistics
            ).outerjoin(
                WordStatistics,
                and_(
                    Word.id == WordStatistics.word_id,
                    WordStatistics.user_id == user.id
                )
            ).filter(
                Word.id.in_(success + failed)
            )
        )
        total_success = 0
        total_failed = 0

        for word, stat in word_stats:
            if stat is None:
                stat = WordStatistics(word_id=word.id, user_id=user.id, success=0, failed=0)
            if word.id in success:
                stat.success += 1
                total_success += 1
            if word.id in failed:
                stat.failed += 1
                total_failed += 1
            db.session.add(stat)

        user_stat = db.session.execute(
            db.select(
                UserStat
            ).filter(
                UserStat.user_id == user.id
            ).filter(
                UserStat.recorded_at == date.today()
            )
        ).scalar_one_or_none()

        if user_stat is None:
           user_stat = UserStat(user_id=user.id, success=total_success, failed=total_failed)
        else:
           user_stat.success += total_success
           user_stat.failed += total_failed

        db.session.add(user_stat)
        db.session.commit()
        return None

    @classmethod
    def get_users_with_aggregate_stat(cls, days :int, count :int = 5) -> Sequence[Tuple[User, int, int, int, int]]:
        agg_stat = db.select(
            UserStat.user_id,
            func.sum(UserStat.success).label('success'),
            func.sum(UserStat.failed).label('failed'), 
            case(
                (func.sum(UserStat.success + UserStat.failed) >= 100, func.sum(UserStat.success + UserStat.failed)),
                else_=0
            ).label('total'),
        ).filter(
            UserStat.recorded_at >= date.today() - timedelta(days=days)
        ).group_by(
            UserStat.user_id
        ).subquery()

        progress_stat = db.select(
            WordStatistics.user_id,
            func.count().label('progress'),
        ).filter(
            WordStatistics.success / (WordStatistics.failed+WordStatistics.success) > 0.75
        ).group_by(
            WordStatistics.user_id
        ).subquery()

        query = db.select(
            User,
            func.coalesce(agg_stat.c.success, 0),
            func.coalesce(agg_stat.c.failed,0),
            func.coalesce(agg_stat.c.total, 0),
            func.coalesce(progress_stat.c.progress, 0),            
        ).outerjoin(
            agg_stat, agg_stat.c.user_id == User.id
        ).outerjoin(
            progress_stat, progress_stat.c.user_id == User.id
        ).order_by(
            progress_stat.c.progress.desc(),
            nulls_last(desc(agg_stat.c.success / func.nullif(agg_stat.c.total, 0))),
            agg_stat.c.total.desc(),
        ).limit(count)

        return db.session.execute(query).all() # type: ignore


    @classmethod
    def get_user_progress(cls, user: User) -> int:
        user_words, = db.session.execute(
            db.select(
                func.count(WordStatistics.word_id)
            ).filter(
                WordStatistics.user_id == user.id,
                WordStatistics.success / (WordStatistics.failed + WordStatistics.success) > 0.75
            )
        ).one()

        return user_words

    @classmethod
    def get_user_tags_stat(cls, user: User, stat_date: date):
        query = db.select(
            UserAggregatedStat
        ).options(
            joinedload(UserAggregatedStat.tag)   
        ).filter(
            UserAggregatedStat.user_id == user.id
        ).filter(
            UserAggregatedStat.recorded_at == stat_date
        ).filter(
            UserAggregatedStat.tag.has()
        ).order_by(
            desc(UserAggregatedStat.failed/UserAggregatedStat.total)
        )
        return db.session.execute(query).unique().scalars()

    @classmethod
    def get_user_topics_stat(cls, user: User):
        words_query = db.select(
            Word.id.label('word_id'),
            cast(func.jsonb_array_elements(Word.tags), Numeric).label('tag_id')
        ).subquery()

        tags_query = db.select(
            Tag.id, 
            func.coalesce(Tag.parent_id, Tag.id).label('root_tag_id')
        ).subquery()

        query =  db.select(
            Tag.id, Tag.description,
            func.sum(WordStatistics.success).label('success'),
            func.sum(WordStatistics.failed).label('failed')
        ).join(
            words_query, WordStatistics.word_id == words_query.c.word_id
        ).join(
            tags_query, words_query.c.tag_id == tags_query.c.id
        ).join(
            Tag, tags_query.c.root_tag_id == Tag.id
        ).filter(
            WordStatistics.user_id == user.id           
        ).group_by(
            Tag.id, Tag.description
        )

        return db.session.execute(query).mappings()
