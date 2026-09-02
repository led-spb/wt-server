from flask import Blueprint, request, current_app as app
from ..models import db
from ..models.word import Tag
from ..services.stats import UserStatService
from dataclasses import dataclass
from datetime import date, timedelta
from marshmallow import Schema, fields
from marshmallow import validate 
from flask_jwt_extended import jwt_required, current_user
from types import SimpleNamespace
from typing import Any

stats_view = Blueprint('stats', __name__)


class AccentSchema(Schema):
    position = fields.Int()

class SpellingSchema(Schema):
    position = fields.Int()
    length = fields.Int()
    variants = fields.List(fields.String())

class WordSchema(Schema):
    id = fields.Int(dump_only=True, required=True)
    fullword = fields.Str(required=True)
    context = fields.Str()
    description = fields.Str()
    level = fields.Int(required=True)
    spellings = fields.Nested(SpellingSchema, many=True)
    accents = fields.Pluck(AccentSchema, 'position', many=True)

class StatisticSchema(Schema):
    success = fields.Int()
    failed = fields.Int()
    total = fields.Method("get_total")
    percent = fields.Method("get_percent")

    def get_total(self, obj):
        return obj.success + obj.failed

    def get_percent(self, obj):
        return obj.success / self.get_total(obj)

class WordStatSchema(StatisticSchema):
    word = fields.Nested(WordSchema)

class DayStatSchema(StatisticSchema):
    recorded_at = fields.Date()

@stats_view.get('')
@jwt_required()
def get_user_stat():
    stats = UserStatService.get_user_stats(current_user, days=14)
    return DayStatSchema().dump(stats, many=True)


@stats_view.get('/words')
@jwt_required()
def get_user_troubles():
    failed_words = UserStatService.get_user_word_failed(current_user, count=10)
    return WordStatSchema().dump(failed_words, many=True)


class UpdateUserStateSchema(Schema):
    failed = fields.List(fields.Int)
    success = fields.List(fields.Int)


@stats_view.put('')
@jwt_required()
def update_user_stat():
    data = UpdateUserStateSchema().load(request.get_json())
    assert data is not None and isinstance(data, dict)

    UserStatService.update_user_stat(
        current_user,
        success_words=data.get('success'), 
        failed_words=data.get('failed')
    )
    return '', 204

class TopicSchema(Schema):
    id = fields.Int()
    description = fields.String(data_key='title')
    type = fields.String()

class TopicsReportSchema(StatisticSchema):
    Tag = fields.Nested("TopicSchema", data_key='topic')

class TopicStatisticsRequestSchema(Schema):
    offset_days = fields.Integer(load_default=0, validate=validate.Range(min=0, max=31))

@stats_view.get('/topics')
@jwt_required()
def get_stats_by_topics():
    args: Any = TopicStatisticsRequestSchema().load(
        request.args,
        many=False,
        unknown='exclude'
    )
    params = SimpleNamespace(**args)
    period_date = date.today() - timedelta(days=params.offset_days)

    data = UserStatService.get_user_topics_stat(
        current_user, 
        for_date = period_date,
        aggregate_topics_root=True
    )
    return TopicsReportSchema().dump(data, many=True)
