from flask import Blueprint
from ..services.words import WordService
from marshmallow import Schema, fields
from flask_jwt_extended import jwt_required


topics_view = Blueprint('topics', __name__)

class TopicSchema(Schema):
    id = fields.Int()
    parent_id = fields.Int()
    description = fields.String()
    type = fields.String()


@topics_view.route('', methods=['GET'])
@jwt_required()
def get_all_tags():
    tags = WordService.get_topics()
    return TopicSchema().dump(tags, many=True)
