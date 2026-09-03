from ..models import db
from ..models.user import User
from ..models.word import  Word
from ..models.stats import WordStatistics, UserStatistics, UserTopicStatistics
from datetime import date, timedelta
from sqlalchemy import func, case, cast, Numeric, desc, nulls_last
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import joinedload
from typing import Sequence, Tuple, List
import itertools

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
    def get_user_stats(cls, user: User, from_date: date = date.today()):
        query = db.select(
            UserStatistics
        ).filter(
            UserStatistics.user_id == user.id,
            UserStatistics.recorded_at >= from_date,
            UserStatistics.recorded_at <= date.today()
        ).order_by(
            desc(UserStatistics.recorded_at)
        )
        return db.session.execute(query)

    @classmethod
    def get_user_topics_stat(cls, user: User, for_date = date.today(), aggregate_topics_root: bool = True):
        ...
        # stat_query = select(
        #     UserTopicSTatistics.recorded_at, 
        #     (UserTopicSTatistics.total-UserTopicSTatistics.failed).label('success') ,
        #     UserTopicSTatistics.failed,
        #     UserTopicSTatistics.tag_id, 
        #     func.coalesce(Tag.parent_id, Tag.id).label('root_tag_id')
        # ).join(
        #     Tag,
        #     UserTopicSTatistics.tag_id == Tag.id
        # ).filter(
        #     UserTopicSTatistics.user_id == user.id,
        #     UserTopicSTatistics.recorded_at.in_((for_date, ))
        # ).subquery()

        # query = select(
        #     Tag, 
        #     stat_query.c.recorded_at, 
        #     func.sum(stat_query.c.success).label('success'),
        #     func.sum(stat_query.c.failed).label('failed'),
        # ).join(
        #     Tag,
        #     stat_query.c.root_tag_id == Tag.id if aggregate_topics_root else stat_query.c.tag_id == Tag.id
        # ).group_by(
        #     Tag.id, stat_query.c.recorded_at
        # ).order_by(
        #     Tag.id, desc(stat_query.c.recorded_at)
        # )
        # return db.session.execute(query)


    @classmethod
    def update_user_stat(cls, user: User, success_words: List[int], failed_words: List[int] ) -> None:
        # search word ids
        words = db.session.execute(
            db.select(Word).filter(Word.id.in_(set(failed_words) | set(success_words)))
        ).scalars().all()

        exists_word_ids = [w.id for w in words]
        # filter input word lists
        success = [id_ for id_ in success_words if id_ in exists_word_ids]
        failed = [id_ for id_ in failed_words if id_ in exists_word_ids]

        if len(success) == 0 and len(failed) == 0:
            return

        cls._update_user_statistics(user, words, success, failed)
        cls._update_word_statistics(user, words, success, failed)
        cls._update_topic_statistics(user, words, success, failed)

        db.session.commit()
        return None

    @classmethod
    def _update_user_statistics(cls, user: User, words: Sequence[Word], success: List[int], failed: List[int]):
        # update user day statistic
        insert_user_stm = insert(
            UserStatistics
        ).values(
            user_id=user.id,
            recorded_at=date.today(),
            success=len(success),
            failed=len(failed),
        )
        update_user_stm = insert_user_stm.on_conflict_do_update(
            index_elements=[UserStatistics.user_id, UserStatistics.recorded_at],
            set_=dict(
                success=UserStatistics.success+insert_user_stm.excluded.success,
                failed=UserStatistics.failed+insert_user_stm.excluded.failed,
            )
        )
        db.session.execute(update_user_stm)
        return None

    @classmethod
    def _update_word_statistics(cls, user: User, words: Sequence[Word], success: List[int], failed: List[int]):
        word_stat = { word_id: {'success':0, 'failed': 0} for word_id in set(success + failed) }
        for word_id in success:
            word_stat[word_id]['success'] += 1
        for word_id in failed:
            word_stat[word_id]['failed'] += 1

        insert_stm = insert(WordStatistics)
        update_stm = insert_stm.on_conflict_do_update(
            index_elements=[WordStatistics.word_id, WordStatistics.user_id],
            set_=dict(
                success=WordStatistics.success + insert_stm.excluded.success,
                failed=WordStatistics.failed + insert_stm.excluded.failed,
            )
        )
        data = [
            {
                'word_id': word_id, 
                'user_id': user.id, 
                'success': info['success'],
                'failed': info['failed']
            } for word_id, info in word_stat.items()
        ]
        db.session.execute(update_stm, data)
        return None

    @classmethod
    def _update_topic_statistics(cls, user: User, words: Sequence[Word], success: List[int], failed: List[int]):
        word_topics = {word.id: word.tags for word in words }
        topics = {
            topic: {'success': 0, 'failed': 0}
            for topic in itertools.chain.from_iterable(word_topics.values())
        }
        for word_id in success:
            for topic_id in word_topics[word_id]:
                topics[topic_id]['success'] += 1
        for word_id in failed:
            for topic_id in word_topics[word_id]:
                topics[topic_id]['failed'] += 1

        print(topics)

        insert_stm = insert(UserTopicStatistics)
        update_stm = insert_stm.on_conflict_do_update(
            index_elements=[UserTopicStatistics.user_id, UserTopicStatistics.recorded_at, UserTopicStatistics.topic_id],
            set_=dict(
                success=UserTopicStatistics.success + insert_stm.excluded.success,
                failed=UserTopicStatistics.failed + insert_stm.excluded.failed,
            )
        )
        data = [
            {
                'user_id': user.id,
                'recorded_at': date.today(),
                'topic_id': topic_id, 
                'success': info['success'],
                'failed': info['failed']
            } for topic_id, info in topics.items()
        ]
        db.session.execute(update_stm, data)
        return None

    @classmethod
    def get_users_with_statistics(cls, days :int, count :int = 5) -> Sequence[Tuple[User, int, int, int, int]]:
        agg_stat = db.select(
            UserStatistics.user_id,
            func.sum(UserStatistics.success).label('success'),
            func.sum(UserStatistics.failed).label('failed'), 
            case(
                (func.sum(UserStatistics.success + UserStatistics.failed) >= 100, func.sum(UserStatistics.success + UserStatistics.failed)),
                else_=0
            ).label('total'),
        ).filter(
            UserStatistics.recorded_at >= date.today() - timedelta(days=days)
        ).group_by(
            UserStatistics.user_id
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
