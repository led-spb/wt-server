from flask import Blueprint, request
from ..models import db, nulls_first, order_random
from ..models.word import db, Word, Spelling, WordStatistics
from ..services.spellings import SpellingService
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
    spellings = fields.Nested(SpellingSchema, many=True, dump_only=True)


@spellings.route('task')
@jwt_required()
def prepare_task():
    min_level = request.args.get('min', 1, type=int)
    max_level = request.args.get('max', 10, type=int)
    count = min(request.args.get('count', 20, type=int), 50)

    failed = SpellingService.get_with_user_stats(
        user=current_user, 
        filters=[
            WordStatistics.failed >0, 
            Word.level >= min_level,
            Word.level <= max_level
        ],
        order_by=[order_random],
        count=count//5
    )

    new = SpellingService.get_with_user_stats(
        user=current_user,
        filters=[
            Word.level >= min_level,
            Word.level <= max_level,
            Word.id.notin_([failed.id for failed in failed])
        ],
        order_by=[
            nulls_first(WordStatistics.success + WordStatistics.failed), 
            order_random
        ],
        count=count - len(failed)
    )

    return WordSpellingSchema().dump(failed+new, many=True)
