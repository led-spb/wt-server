import json
import logging
import click
from typing import List
from flask import current_app
from flask.cli import AppGroup
from sqlalchemy import func, distinct, cast, Numeric, or_
from sqlalchemy.orm import join, joinedload
from ..models import db
from ..models.user import User
from ..models.word import Word, Spelling, Accent, WordStatistics, Tag
from ..models.stats import UserAggregatedStat
from ..services.users import UserService
from ..services.stats import UserStatService
import pywebpush
import itertools
from datetime import date, timedelta
from dataclasses import dataclass
from typing import Sequence

tools_commands = AppGroup('tools', help='Custom tools')


@tools_commands.command('merge_words', help='Merge duplicated words')
@click.argument('count', default=10, type=int)
def exec_merge_words(count :int):

    distinct_count = func.count().label('distinct_count')

    query = db.select(
        Word.fullword, Word.context, distinct_count
    ).group_by(
        Word.fullword, Word.context,
    ).having(
        distinct_count > 1
    ).limit(
        count
    )

    for item in db.session.execute(query).all():
        current_app.logger.warning(f'{item[0]}/{item[1]}: {item[2]}')

        query = db.select(
            Word
        ).options(
            joinedload(Word.spellings),
            joinedload(Word.accents)
        ).filter(
            Word.fullword == item[0],
            Word.context == item[1],
        )

        words :Sequence[Word] = db.session.execute(query).unique().scalars().all()

        new_word = merge_words(words)
        assert new_word is not None
        update_words_stats(words, new_word)
        cascade_delete_words(words)
    pass


def merge_words(words :Sequence[Word]) -> Word|None:
    if len(words) == 0:
        return None

    new_word = Word(
        fullword=words[0].fullword,
        context=words[0].context,
        level=min(words, key=lambda x: x.level).level,
        tags=list(set(itertools.chain(*[w.tags for w in words if w.tags is not None]))),
        rules=list(set(itertools.chain(*[w.rules for w in words if w.rules is not None]))),
    )

    spellings = itertools.chain.from_iterable(
        map(lambda x: x.spellings, words)
    )
    for sp in spellings:
        current_sp = next(filter(
            lambda x: sp.position == x.position and sp.length == x.length,
            new_word.spellings
        ), None)
        if current_sp is None:
            current_sp = Spelling(
                position=sp.position,
                length=sp.length,
                variants=sp.variants
            )
            new_word.spellings.append(current_sp)
        else:
            pass

    accents = set(
        map(
            lambda x: x.position,
            itertools.chain.from_iterable(map(lambda x: x.accents, words))
        )
    )
    for acc_position in accents:
        new_word.accents.append(
            Accent(position=acc_position)
        )

    db.session.add(new_word)
    db.session.commit()
    return new_word


def update_words_stats(words :Sequence[Word], new_word: Word):
    stats = db.session.execute(
        db.select(
            WordStatistics.user_id,
            func.sum(WordStatistics.success),
            func.sum(WordStatistics.failed)
        ).filter(
            WordStatistics.word_id.in_([w.id for w in words])
        ).group_by(
            WordStatistics.user_id
        )
    ).all()

    for user_id, success, failed in stats:
        user_stat = db.session.execute(
            db.select(
                WordStatistics
            ).filter(
                WordStatistics.word_id == new_word.id,
                WordStatistics.user_id == user_id
            )
        ).scalar_one_or_none()

        if user_stat is None:
            user_stat = WordStatistics(
                word_id=new_word.id,
                user_id=user_id,
                success=success,
                failed=failed
            )
        else:
            user_stat.success += success
            user_stat.failed += failed
        db.session.add(user_stat)

def cascade_delete_words(words :Sequence[Word]):
    for word in words:
        statistics = db.session.execute(
            db.select(WordStatistics).filter(WordStatistics.word_id == word.id)
        ).scalars().all()

        for item in statistics:
            db.session.delete(item)

        db.session.delete(word)
        db.session.commit()

@tools_commands.command('notify')
@click.argument('email', type=str)
@click.argument('message', type=str)
def notify(email: str, message: str):
    user = UserService.get_user_by_email(email)
    assert user is not None

    logging.warning(f'User: {user.name}')

    push = next(iter(sorted(user.pushes, reverse=True, key=lambda p: p.created_at)), None)
    logging.warning(f'Push: {push}')
    if push is None:
        return

    pywebpush.webpush(
        subscription_info=json.loads(push.push_info),
        data=json.dumps(dict(title='Тренажер слов', body=message)),
        vapid_private_key=current_app.config.get('VAPID_PRIVATE_KEY'),
        vapid_claims={
            "sub": "mailto:{0}".format(current_app.config.get('ADMIN_EMAIL'))
        }
    )


@tools_commands.command('gather', help='Gather user statistics')
def gather_statistics():
    db.session.execute(
        db.delete(
            UserAggregatedStat
        ).filter(
            or_(
                UserAggregatedStat.recorded_at == date.today(),
                UserAggregatedStat.recorded_at < date.today() - timedelta(days=60)
            )
        )
    )

    words_query = db.select(
        Word.id.label('word_id'),
        cast(func.jsonb_array_elements(Word.tags), Numeric).label('tag_id')
    ).subquery()

    query = db.select(
        WordStatistics.user_id,
        Tag.id.label('tag_id'),
        func.sum(WordStatistics.success+WordStatistics.failed).label('total'),
        func.sum(WordStatistics.failed).label('failed')
    ).join(
        words_query, WordStatistics.word_id == words_query.c.word_id
    ).join(
        Tag, words_query.c.tag_id == Tag.id
    ).group_by(
        WordStatistics.user_id, Tag.id, Tag.description
    )

    db.session.execute(
        db.insert(UserAggregatedStat).from_select(["user_id", "tag_id", "total", "failed"], query)
    )
    db.session.commit()
    pass
