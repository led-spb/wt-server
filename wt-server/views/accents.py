from flask import Blueprint, request, current_app as app
from marshmallow import Schema, fields
from ..models import db, order_random, nulls_first
from ..models.word import Word, Accent, WordStatistics
from ..services.words import WordService
from ..services.accents import AccentService
from .words import WordSchema
from flask_jwt_extended import jwt_required, current_user


accents = Blueprint('accents', __name__)


class AccentImportSchema(Schema):
    words = fields.List(fields.String, required=True)
    level = fields.Int(required=True)

class AccentPositionSchema(Schema):
    position = fields.Int()
    
class AccentSchema(WordSchema):
    accents = fields.Pluck(AccentPositionSchema, 'position', many=True)

class AccentImportResultSchema(Schema):
    results = fields.Nested(AccentSchema, many=True)


#@accents.route('/import', methods=['POST'])
def import_accent():
    data = AccentImportSchema().load(
        request.get_json()
    )
    word_level = data.get('level', 6)

    results = []
    for item in data.get('words', []):
        accent_position = next((idx for idx, chr in enumerate(item) if chr.isupper()), None)
        word = None
        if accent_position is not None:
            word = WordService.find_by_name(item.lower())
            if word is None:
                word = Word(fullword=item.lower(), level=word_level)
                db.session.add(word)

            acc_positions = [acc.position for acc in word.accents]
            if accent_position not in acc_positions:
                word.accents.append(
                    Accent(word_id=word.id, position=accent_position)
                )
                db.session.add(word)
        results.append(word)

    db.session.commit()
    return AccentImportResultSchema().dump({'results': results}), 200


@accents.route('/task', methods=['GET'])
@jwt_required()
def prepare_task():
    min_level = request.args.get('min', 1, type=int)
    max_level = request.args.get('max', 10, type=int)
    count = min(request.args.get('count', 20, type=int), 50)

    failed = AccentService.get_with_user_stats(
        user=current_user, 
        filters=[
            WordStatistics.failed >0, 
            Word.level >= min_level,
            Word.level <= max_level
        ],
        order_by=[order_random],
        count=count//5
    )

    new = AccentService.get_with_user_stats(
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

    return AccentSchema().dump(failed+new, many=True)
