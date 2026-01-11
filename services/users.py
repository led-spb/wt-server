from typing import Union, List, Tuple
from models import db
from models.user import User, UserStat
from models.word import Word
from datetime import date, timedelta
from sqlalchemy import func, cast, Integer, desc, column
from sqlalchemy.dialects.postgresql import JSONB


class UserService:
    @classmethod
    def get_user_by_id(cls, id :int) -> Union[User, None]:
        return db.session.execute(
            db.select(User).filter(User.id == id)
        ).scalar_one_or_none()
    
    @classmethod
    def get_user_by_login(cls, login :str) -> Union[User, None]:
        return db.session.execute(
            db.select(User).filter(User.name == login)
        ).scalar_one_or_none()


class UserStatService:

    @classmethod
    def get_user_failed_words(cls, user: User, days :int, count :int) -> List[Tuple[Word, int]]:
        failed_query = db.select(
            func.jsonb_array_elements(
                cast(UserStat.failed, JSONB)
            ).label('word_id').cast(Integer),
            func.count().label('frequency')
        ).filter(
            UserStat.user_id == user.id
        ).filter(
            UserStat.recorded_at >= date.today() - timedelta(days=days)
        ).group_by('word_id').order_by(
            desc('frequency')
        ).limit(count).subquery()

        words_query = db.select(
            Word, 
            failed_query.c.frequency
        ).join(failed_query, Word.id == failed_query.c.word_id)

        return db.session.execute(words_query).all()


    @classmethod
    def get_user_stats(cls, user: User, days :int):
        stat_query = db.select(
            UserStat.user_id,
            UserStat.recorded_at,
            func.jsonb_array_elements(
                cast(UserStat.success, JSONB)
            ).label('success_id').cast(Integer),
            func.jsonb_array_elements(
                cast(UserStat.failed, JSONB)
            ).label('failed_id').cast(Integer)
        ).filter(
            UserStat.user_id == user.id
        ).filter(
            UserStat.recorded_at >= date.today() - timedelta(days=days)
        ).subquery()

        query = db.select(
            User.id, 
            stat_query.c.recorded_at,
            func.count(stat_query.c.success_id).label('success'),
            func.count(stat_query.c.failed_id).label('failed')
        ).join(
            stat_query, User.id == stat_query.c.user_id
        ).group_by(
            User.id,
            stat_query.c.recorded_at
        )

        return db.session.execute(query).all()
        

    @classmethod
    def update_user_stat(cls, user: User, success: List[int], failed: List[int]) -> None:
        stat = db.session.execute(
            db.select(UserStat)
            .filter_by(user_id=User.id)
            .filter_by(recorded_at=date.today())
        ).scalar_one_or_none()

        if stat is None:
            stat = UserStat(user_id=user.id, success=success, failed=failed)
        else:
            stat.success = stat.success + success
            stat.failed = stat.failed + failed

        db.session.add(stat)
        db.session.commit()
        return None
