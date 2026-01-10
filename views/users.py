from flask import Blueprint, jsonify, request, current_app as app
from models.user import db, User, UserStat
from models.words import Word
from marshmallow import Schema, fields
from datetime import date
from flask_jwt_extended import jwt_required, current_user
from sqlalchemy import func, cast, Integer, desc, column
from .words import WordSchema
from sqlalchemy.dialects.postgresql import JSONB


users = Blueprint('users', __name__)

class UserSchema(Schema):
    id = fields.Int(required=True, dump_only=True)
    name = fields.Str(required=True)


@users.route('', methods=['GET'])
@jwt_required()
def get_user_info():
    return UserSchema().dump(current_user)

class WordStatSchema(Schema):
    word = fields.Nested(WordSchema)
    frequency = fields.Int()

class UserStatSchema(Schema):
    failed = fields.Nested(WordStatSchema, many=True)


@users.route('/stat', methods=['GET'])
@jwt_required()
def get_user_stat():
    failed_query = db.select(
        func.jsonb_array_elements(cast(UserStat.failed, JSONB)).label('word_id').cast(Integer),
        func.count().label('frequency')
    ).filter_by(
        user_id=current_user.id
    ).group_by('word_id').order_by(
        desc('frequency')
    ).limit(10).subquery()

    words_query = db.select(
        Word, failed_query.c.frequency
    ).join(failed_query, Word.id == failed_query.c.word_id)

    top_failed = [ {'word': word, 'frequency': frequency} for word, frequency in db.session.execute(words_query).all()]

    return UserStatSchema().dump({'failed': top_failed})


@users.route('/stat', methods=['PUT'])
@jwt_required()
def update_user_stat():
    data = UserStatSchema().load(request.get_json())

    stat = db.session.execute(
        db.select(UserStat).filter_by(user_id=current_user.id).filter_by(recorded_at=date.today())
    ).scalar_one_or_none()

    if stat is None:
        stat = UserStat(user_id=current_user.id, success=[], failed=[])

    success = stat.success[:]
    success.extend(data['success'])

    failed = stat.failed[:]
    failed.extend(data['failed'])

    stat.success = success
    stat.failed = failed

    db.session.add(stat)
    db.session.commit()

    return '', 204
