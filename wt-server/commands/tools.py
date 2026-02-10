import json
import logging
import click
from typing import List
from flask import current_app
from flask.cli import AppGroup
from sqlalchemy import func, distinct
from sqlalchemy.orm import join, joinedload
from ..models import db
from ..models.user import User
from ..models.word import Word, Spelling, Accent, WordStatistics
from ..models.stats import UserAggregatedStat
from ..services.users import UserService
from ..services.stats import UserStatService
import pywebpush
import itertools
from datetime import date, timedelta
from dataclasses import dataclass

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

        words = db.session.execute(query).unique().scalars().all()

        new_word = merge_words(words)
        update_words_stats(words, new_word)
        cascade_delete_words(words)
    pass


def merge_words(words :List[Word]) -> Word:
    if len(words) == 0:
        return None

    new_word = Word(
        fullword=words[0].fullword,
        context=words[0].context,
        level=min(words, key=lambda x: x.level).level,
        description=min([w.description for w in words if w.description is not None], key=len, default=None),
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


def update_words_stats(words :List[Word], new_word: Word):
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

def cascade_delete_words(words :List[Word]):
    for word in words:
        statistics = db.session.execute(
            db.select(WordStatistics).filter(WordStatistics.word_id == word.id)
        ).scalars().all()

        for item in statistics:
            db.session.delete(item)

        db.session.delete(word)
        db.session.commit()

@tools_commands.command('notify')
@click.argument('login', type=str)
@click.argument('message', type=str)
def notify(login: str, message: str):
    user = UserService.get_user_by_login(login)
    logging.warning(f'User: {user.name}')
    if user is None:
        return

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


@dataclass
class Stat:
    total: int
    failed: int

@tools_commands.command('gather', help='Gather user statistics')
def gather_statistics():
    all_users = db.session.execute(
        db.select(User)
    ).scalars()
    for user in all_users:
        gather_user_stistics(user, date.today())
    pass


def gather_user_stistics(user :User, stat_date :date):
    tags = dict()
    rules = dict()

    db.session.execute(
        db.delete(
            UserAggregatedStat
        ).filter(
            UserAggregatedStat.user_id == user.id
        ).filter(
            UserAggregatedStat.recorded_at == stat_date
        )
    )
    for info in UserStatService.get_user_words_statistics(user):
        for tag_id in info.word.tags or []:
            if tag_id not in tags:
                tags[tag_id] = Stat(0, 0)
            tags[tag_id].total += info.failed+info.success
            tags[tag_id].failed += info.failed
        for rule_id in info.word.rules or []:
            if rule_id not in rules:
                rules[rule_id] = Stat(0, 0)
            rules[rule_id].total += info.failed+info.success
            rules[rule_id].failed += info.failed

    for tag_id, stat in tags.items():
        db.session.add(
            UserAggregatedStat(
                user_id=user.id,
                tag_id=tag_id,
                total=stat.total,
                failed=stat.failed,
                recorded_at=stat_date,
            )
        )
    #for rule_id, stat in rules.items():
    #    db.session.add(
    #        UserAggregatedStat(
    #            user_id=user.id,
    #            rule_id=rule_id,
    #            total=stat.total,
    #            failed=stat.failed,
    #            recorded_at=stat_date,
    #        )
    #    )
    db.session.commit()
