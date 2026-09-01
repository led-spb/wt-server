from flask import Blueprint
from ..services.words import WordService
from marshmallow import Schema, fields
from flask_jwt_extended import jwt_required


tags_view = Blueprint('tags', __name__)

class TagsSchema(Schema):
    id = fields.Int()
    parent_id = fields.Int()
    description = fields.String()
    type = fields.String()


@tags_view.route('', methods=['GET'])
@jwt_required()
def get_all_tags():
    tags = WordService.get_tags_dictonary()
    return TagsSchema().dump(tags, many=True)
