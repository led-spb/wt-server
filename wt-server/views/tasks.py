from flask import Blueprint, request, current_app
from ..models import db, nulls_first, order_random, order_desc
from ..models.word import Word, Spelling
from ..models.stats import WordStatistics
from ..services.stats import UserStatService
from ..services.words import WordService
from marshmallow import Schema, fields
from flask_jwt_extended import jwt_required, current_user
from sqlalchemy import or_


tasks_view = Blueprint('tasks', __name__)


class SpellingSchema(Schema):
    id = fields.Int(required=True, dump_only=True)
    position = fields.Int(required=True)
    length = fields.Int(required=True)
    variants = fields.List(fields.Str())

class AccentPositionSchema(Schema):
    position = fields.Int()

class WordSchema(Schema):
    id = fields.Int(dump_only=True, required=True)
    fullword = fields.Str(required=True)
    context = fields.Str()
    description = fields.Str()
    level = fields.Int(required=True)
    rules = fields.List(fields.Integer())
    tags = fields.List(fields.Integer())
    spellings = fields.Nested(SpellingSchema, many=True, dump_only=True)
    accents = fields.Pluck(AccentPositionSchema, 'position', many=True)

class TaskSchema(Schema):
    Word = fields.Nested(WordSchema)

@tasks_view.route('')
@jwt_required()
def prepare_task():
    count = min(request.args.get('count', 20, type=int), 50)
    # errors = min(request.args.get('errors', 0, type=int), count)
    topics = request.args.getlist('topics[]', int)

    filters = []
    if len(topics) > 0:
        filters.append(
            or_(*[Word.tags.contains([tag]) for tag in topics])
        )

    data = UserStatService.get_user_words(
        current_user,
        count,
        filters,
        [order_desc(WordStatistics.failed)]
    ).scalars()
    return WordSchema().dump(data, many=True)
