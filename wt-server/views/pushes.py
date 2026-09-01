from ..services.pushes import WebPushService
from flask import Blueprint, request, jsonify, current_app as app
from flask_jwt_extended import jwt_required, current_user
from marshmallow import Schema, fields


pushes_view = Blueprint('pushes', __name__)


class SubscriptionKeysSchema(Schema):
    auth = fields.String(required=True)
    p256dh = fields.String(required=True)

class SubscriptionSchema(Schema):
    endpoint = fields.Url(required=True)
    expirationTime = fields.Integer(allow_none=True)
    keys = fields.Nested(SubscriptionKeysSchema, required=True)

@pushes_view.route('/register', methods=['POST'])
@jwt_required()
def register():
    data = SubscriptionSchema().load(request.get_json(), many=False)
    assert data is not None and isinstance(data, dict)

    WebPushService.register_web_push(current_user, data)
    return '', 204


@pushes_view.route('/unregister', methods=['POST'])
@jwt_required()
def unregister():
    data = SubscriptionSchema().load(request.get_json(), many=True)
    assert data is not None and isinstance(data, dict)

    WebPushService.unregister_web_push(current_user, data)
    return '', 204


class SubscriptionInfoSchema(Schema):
    public_key = fields.String(data_key='publicKey')

@pushes_view.get('/key')
@jwt_required()
def get_subscription_key():
    return SubscriptionInfoSchema().dump(dict(public_key=app.config.get('VAPID_PUBLIC_KEY')))
