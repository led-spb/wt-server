from flask import Blueprint, jsonify, request, current_app as app

from services.users import UserStatService
from marshmallow import Schema, fields
from flask_jwt_extended import jwt_required, current_user
from .words import WordSchema


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

class DayStatSchema(Schema):
    recorded_at = fields.Date()
    success = fields.Int()
    failed = fields.Int()

class UserStatSchema(Schema):
    failed = fields.Nested(WordStatSchema, many=True)
    days = fields.Nested(DayStatSchema, many=True)

class UpdateUserStateSchema(Schema):
    failed = fields.List(fields.Int)
    success = fields.List(fields.Int)


@users.route('/stat', methods=['GET'])
@jwt_required()
def get_user_stat():
    failed_words = UserStatService.get_user_failed_words(current_user, days=14, count=10)
    failed = [dict(word=word, frequency=frequency) for (word, frequency) in failed_words]

    stats = UserStatService.get_user_stats(current_user, days=14)

    app.logger.error(f'{type(failed)}, {failed}')
    return UserStatSchema().dump({
        'failed': failed,
        'days': stats
    })


@users.route('/stat', methods=['PUT'])
@jwt_required()
def update_user_stat():
    data = UpdateUserStateSchema().load(
        request.get_json()
    )
    UserStatService.update_user_stat(current_user, success=data['success'], failed=data['failed'])
    return '', 204
