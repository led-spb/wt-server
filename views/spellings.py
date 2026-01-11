from flask import Blueprint, request
from models.word import db, Word, Spelling
from services.tasks import TaskService
from sqlalchemy import func
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


def get_word_spellings(word_id):
     items = Spelling.query.filter(Spelling.word_id == word_id)
     return SpellingSchema().dump(items, many=True)


def create_word_spelling(word_id):
     word = Word.query.get_or_404(word_id)

     data = SpellingSchema().load(request.get_json())
     spelling = Spelling(**data)
     spelling.word_id = word.id
     db.session.add(spelling)
     db.session.commit()

     return get_word_spellings(word_id)


def delete_word_spelling(id):
    part = Spelling.query.get_or_404(id)
    db.session.delete(part)
    db.session.commit()
    return '', 204


@spellings.route('task')
@jwt_required()
def prepare_task():
    min_level = request.args.get('min', 1, type=int)
    max_level = request.args.get('max', 10, type=int)
    count = min(request.args.get('count', 20, type=int), 50)

    task = TaskService.get_user_spelling_task(current_user, count=count, min_level=min_level, max_level=max_level)

    return WordSpellingSchema().dump(task, many=True)
