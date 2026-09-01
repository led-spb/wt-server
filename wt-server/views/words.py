from flask import Blueprint, abort, request
from marshmallow import Schema, fields
from ..services.words import WordService
from flask_jwt_extended import jwt_required

words_view = Blueprint('words', __name__)


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


@words_view.route('<int:word_id>', methods=['GET'])
@jwt_required()
def get_word(word_id: int):
    word = WordService.get_by_id(word_id)
    if word is None:
        abort(404)
    return WordSchema().dump(word)


@words_view.route('', methods=['GET'])
@jwt_required()
def get_word_by_name():
    name = request.args.get('name', None, type=str)
    if name is None:
        abort(400)

    word = WordService.find_by_name(name.lower())
    if word is None:
        abort(404)
    return WordSchema().dump(word)
