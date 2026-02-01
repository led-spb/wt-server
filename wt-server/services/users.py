from typing import Union, List
from ..models import db
from ..models.user import User, UserStat
from ..models.word import WordStatistics, Word
from .invites import InvitesService
from datetime import date, timedelta
from sqlalchemy import func, case, cast, Numeric, desc, and_, nulls_last
from sqlalchemy.orm import joinedload


class UserService:

    @classmethod
    def get_user_by_id(cls, id :int) -> Union[User, None]:
        return db.session.execute(
            db.select(User).filter(User.id == id)
        ).scalar_one_or_none()

    @classmethod
    def get_user_by_login(cls, login :str) -> Union[User, None]:
        return db.session.execute(
            db.select(User).filter(User.login == login)
        ).scalar_one_or_none()
    
    @classmethod
    def register_user(cls, login :str, password :str, invite :str|None) -> User:
        new_user = User(login=login, name=login)
        new_user.set_password(password)
        db.session.add(new_user)
        
        if invite is not None:
            InvitesService.redeem_invite(invite, new_user)
        db.session.commit()
        return new_user


class UserStatService:

    @classmethod
    def get_user_word_failed(cls, user: User, count :int) -> List[WordStatistics]:
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
    def get_user_stats(cls, user: User, days :int|None = None) -> List[UserStat]:
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
    def update_user_stat(cls, user: User, success: List[int], failed: List[int]) -> None:
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
    def get_users_with_aggregate_stat(cls, days :int, count :int = 5) -> List[tuple[User, int, int, int, int]]:
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

        return db.session.execute(query).all()


    @classmethod
    def get_user_progress(cls, user: User) -> int:
        user_words, = db.session.execute(
            db.select(
                func.count(WordStatistics.word_id)
            ).filter(
                WordStatistics.user_id == user.id,
                WordStatistics.success / (WordStatistics.failed + WordStatistics.success) > 0.75
            )
        ).one_or_none()

        return user_words
