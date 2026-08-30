from flask import Blueprint, abort, request, current_app as app, jsonify
from marshmallow import Schema, fields
from ..models import db
from ..models.word import Rule
from ..services.words import WordService
from flask_jwt_extended import jwt_required, current_user

rules = Blueprint('rules', __name__)


class RuleSchema(Schema):
    id = fields.Integer()
    description = fields.String()
    title = fields.String()
    type = fields.String()

class RulePageSchema(Schema):
    total = fields.Integer()
    page = fields.Integer()
    pages = fields.Integer()
    items = fields.Nested(RuleSchema, exclude=['description'], many=True)

@rules.route('<int:rule_id>', methods=['GET'])
@jwt_required()
def get_rule(rule_id: int):
    rule = WordService.get_rule_by_id(rule_id)
    if rule is None:
        abort(404)
    return RuleSchema().dump(rule)


@rules.route('', methods=['GET'])
@jwt_required()
def get_rules():
    page = max(request.args.get('page', type=int, default=1), 1)
    limit = max( min(request.args.get('limit', type=int, default=10), 20), 1)
    title = request.args.get('title', type=str, default=None)

    page = WordService.search_rules(title, page, limit)
    return RulePageSchema().dump(page)
