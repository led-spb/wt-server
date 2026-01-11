from flask import Blueprint, request
from models.word import db, Word
from marshmallow import Schema, fields


words = Blueprint('words', __name__)


class WordSchema(Schema):
    id = fields.Int(dump_only=True, required=True)
    fullword = fields.Str(required=True)
    context = fields.Str()
    description = fields.Str()
    level = fields.Int(required=True)


class SearchWordSchema(Schema):
    ids = fields.List['int']


def get_words():
    items = db.paginate(
        Word.query.order_by(Word.id), page=1, per_page=20
    )
    return WordSchema().dump(items, many=True)


def get_word(id):
    word = Word.query.get_or_404(id)
    return WordSchema().dump(word)


def create_word():
    data = WordSchema().load(request.get_json())
    item = Word(**data)

    db.session.add(item)
    db.session.commit()

    return WordSchema().dump(item)


def delete_words(id):
    word = Word.query.get_or_404(id)
    db.session.delete(word)
    db.session.commit()
    return '', 204


@words.route('search', methods=['POST'])
def search_words():
    data = SearchWordSchema().load(request.get_json())   
    return '', 201
