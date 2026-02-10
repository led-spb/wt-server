from flask import Blueprint, request, current_app
from ..models import db, nulls_first, order_random, order_desc
from ..models.word import Word, Spelling, WordStatistics
from ..services.spellings import SpellingService
from ..services.words import WordService
from marshmallow import Schema, fields
from flask_jwt_extended import jwt_required, current_user

spellings = Blueprint('spellings', __name__)


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


@spellings.route('task')
@jwt_required()
def prepare_task():
    level = request.args.get('level', 10, type=int)
    count = min(request.args.get('count', 20, type=int), 50)
    errors = min(request.args.get('errors', 0, type=int), count)
    tags = request.args.getlist('tags[]', int)

    failed = SpellingService.get_with_user_stats(
        user=current_user, 
        filters=[
            WordStatistics.failed >0, 
            Word.level <= level,
            Word.tags.contains(tags),
        ],
        order_by=[WordStatistics.success/WordStatistics.failed, order_desc(WordStatistics.failed), order_random()],
        count=errors
    )

    new = SpellingService.get_with_user_stats(
        user=current_user,
        filters=[
            Word.level <= level,
            Word.id.notin_([failed.id for failed in failed]),
            Word.tags.contains(tags),
        ],
        order_by=[
            nulls_first(WordStatistics.success + WordStatistics.failed), 
            order_random()
        ],
        count=count - len(failed)
    )

    return WordSpellingSchema().dump(failed+new, many=True)
