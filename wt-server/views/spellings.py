from flask import Blueprint, request, current_app
from ..models import db, nulls_first, order_random, order_desc
from ..models.word import Word, Spelling, WordStatistics
from ..services.spellings import SpellingService
from ..services.words import WordService
from marshmallow import Schema, fields
from flask_jwt_extended import jwt_required, current_user
from sqlalchemy import or_


spellings_view = Blueprint('spellings', __name__)


class SpellingSchema(Schema):
    id = fields.Int(required=True, dump_only=True)
    position = fields.Int(required=True)
    length = fields.Int(required=True)
    variants = fields.List(fields.Str())


class WordSpellingSchema(Schema):
    id = fields.Int(dump_only=True, required=True)
    fullword = fields.Str(required=True)
    context = fields.Str()
    description = fields.Str()
    level = fields.Int(required=True)
    rules = fields.List(fields.Integer())
    tags = fields.List(fields.Integer())
    spellings = fields.Nested(SpellingSchema, many=True, dump_only=True)


@spellings_view.route('task')
@jwt_required()
def prepare_task():
    level = request.args.get('level', 10, type=int)
    count = min(request.args.get('count', 20, type=int), 50)
    errors = min(request.args.get('errors', 0, type=int), count)
    tags = request.args.getlist('tags[]', int)

    default_filters = [Word.level <= level,]
    if len(tags) > 0:
        default_filters.append(
            or_(*[Word.tags.contains([tag]) for tag in tags])
        )

    failed = SpellingService.get_with_user_stats(
        user=current_user, 
        filters=default_filters + [ WordStatistics.failed >0, ],
        order_by=[WordStatistics.success/WordStatistics.failed, order_desc(WordStatistics.failed), order_random()],
        count=errors
    )    

    new = SpellingService.get_with_user_stats(
        user=current_user,
        filters=default_filters + [ Word.id.notin_([failed.id for failed in failed]), ],
        order_by=[
            nulls_first(WordStatistics.success + WordStatistics.failed), 
            order_random()
        ],
        count=count - len(failed)
    )

    return WordSpellingSchema().dump(
        list(failed)+list(new), 
        many=True
    )
