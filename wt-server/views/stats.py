from flask import Blueprint, request, current_app as app
from ..models import db
from ..services.stats import UserStatService
from datetime import date, timedelta
from marshmallow import Schema, fields
from flask_jwt_extended import jwt_required, current_user


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


class TagSchema(Schema):
    id = fields.Int()
    description = fields.String(data_key='title')
    type = fields.String()


class TagsStatisticsSchema(Schema):
    tag = fields.Nested(TagSchema)
    total = fields.Integer()
    failed = fields.Integer()
    prev = fields.Nested("TagsStatisticsSchema", only=['total', 'failed'])


@stats_view.get('/tags')
@jwt_required()
def get_stats_by_tags():
    #current_period = date.today() - timedelta(days=date.today().weekday())
    #last_period = current_period - timedelta(days=7)
    current_period = date.today()
    last_period = current_period - timedelta(days=1)

    current = list(UserStatService.get_user_tags_stat(current_user, current_period))
    prev = {info.tag.id: info for info in UserStatService.get_user_tags_stat(current_user, last_period)}

    for curr in current:
       curr.prev = prev.get(curr.tag.id)
  
    return TagsStatisticsSchema().dump(current, many=True)


class TopicsReportSchema(StatisticSchema):
    id = fields.Int()
    description = fields.Str()


@stats_view.get('/topics')
@jwt_required()
def get_stats_by_topics():
    data = UserStatService.get_user_topics_stat(current_user)
    return TopicsReportSchema().dump(data, many=True)
