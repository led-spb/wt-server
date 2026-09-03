from flask import Blueprint, request, current_app as app
from ..models import db
from ..services.stats import UserStatService
from dataclasses import dataclass
from datetime import date, timedelta
from marshmallow import Schema, fields, post_dump
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
    @post_dump
    def remove_skip_values(self, data, **kwags):
        return {
            key: value for key, value in data.items()
            if value is not None
        }

    success = fields.Int()
    failed = fields.Int()
    total = fields.Method("get_total")
    percent = fields.Method("get_percent")

    def get_total(self, obj):
        if obj is None or obj.success is None or obj.failed is None:
            return None
        return obj.success + obj.failed

    def get_percent(self, obj):
        if obj is None or obj.success is None:
            return None
        total = self.get_total(obj)
        if total == 0:
            return 0
        return obj.success / total

class WordStatSchema(StatisticSchema):
    word = fields.Nested(WordSchema)

class DayStatSchema(StatisticSchema):
    recorded_at = fields.Date()

class StatisticsRequestSchema(Schema):
    days = fields.Integer(load_default=7, validate=validate.Range(min=0, max=31))


@stats_view.get('')
@jwt_required()
def get_user_stat():
    args: Any = StatisticsRequestSchema().load(
        request.args,
        many=False,
        unknown='exclude'
    )
    params = SimpleNamespace(**args)
    data = UserStatService.get_user_stats(
        current_user, 
        from_date = date.today() - timedelta(days=params.days)
    ).scalars()
    return DayStatSchema().dump(data, many=True)


@stats_view.get('/words')
@jwt_required()
def get_user_troubles():
    failed_words = UserStatService.get_user_word_failed(current_user, count=10)
    return WordStatSchema().dump(failed_words, many=True)


class UpdateUserStateSchema(Schema):
    failed = fields.List(fields.Int, load_default=[])
    success = fields.List(fields.Int, load_default=[])


@stats_view.put('')
@jwt_required()
def update_user_stat():
    data = UpdateUserStateSchema().load(request.get_json())

    assert data is not None and isinstance(data, dict)
    params = SimpleNamespace(**data)

    UserStatService.update_user_stat(
        user=current_user,
        success_words=params.success,
        failed_words=params.failed, 
    )
    return '', 204

class TopicSchema(Schema):
    id = fields.Int()
    description = fields.String(data_key='title')
    type = fields.String()

class TopicsReportSchema(StatisticSchema):
    Tag = fields.Nested("TopicSchema", data_key='topic')

@stats_view.get('/topics')
@jwt_required()
def get_user_stats_by_topics():
    args: Any = StatisticsRequestSchema().load(
        request.args,
        many=False,
        unknown='exclude'
    )
    params = SimpleNamespace(**args)
    period_date = date.today() - timedelta(days=params.days)

    data = UserStatService.get_user_topics_stat(
        current_user, 
        for_date = period_date,
        aggregate_topics_root=True
    ) or []
    return TopicsReportSchema().dump(data, many=True)
