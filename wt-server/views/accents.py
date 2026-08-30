from flask import Blueprint, request, current_app as app
from marshmallow import Schema, fields
from ..models import db, order_random, nulls_first, order_desc
from ..models.word import Word, Accent, WordStatistics
from ..services.words import WordService
from ..services.accents import AccentService
from flask_jwt_extended import jwt_required, current_user
from sqlalchemy import or_


accents = Blueprint('accents', __name__)


class AccentPositionSchema(Schema):
    position = fields.Int()


class WordAccentAccentSchema(Schema):
    id = fields.Int(dump_only=True, required=True)
    fullword = fields.Str(required=True)
    context = fields.Str()
    description = fields.Str()
    level = fields.Int(required=True)
    rules = fields.List(fields.Integer())
    tags = fields.List(fields.Integer())
    accents = fields.Pluck(AccentPositionSchema, 'position', many=True)


@accents.route('/task', methods=['GET'])
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

    failed = AccentService.get_with_user_stats(
        user=current_user, 
        filters=default_filters + [ WordStatistics.failed > 0, ],
        order_by=[WordStatistics.success/WordStatistics.failed, order_desc(WordStatistics.failed), order_random()],
        count=errors
    )

    new = AccentService.get_with_user_stats(
        user=current_user,
        filters=default_filters + [ Word.id.notin_([failed.id for failed in failed]), ],
        order_by=[
            nulls_first(WordStatistics.success + WordStatistics.failed), 
            order_random()
        ],
        count=count - len(failed)
    )

    return WordAccentAccentSchema().dump(failed+new, many=True)
