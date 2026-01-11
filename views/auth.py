from services.users import UserService
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, set_access_cookies, unset_access_cookies
from marshmallow import Schema, fields


auth = Blueprint('auth', __name__)

def user_identity_lookup(user):
    return str(user.id)

def user_lookup(identity):
    return UserService.get_user_by_id(identity)

class UserLoginSchema(Schema):
    login = fields.String(required=True)
    password = fields.String(required=True)

@auth.route('/token', methods=['POST'])
def token():
    data = UserLoginSchema().load(
        request.get_json()
    )

    auth_user = UserService.get_user_by_login(data.get('login'))
    if auth_user is not None and auth_user.check_password(data.get('password')):
        access_token = create_access_token(identity=auth_user)
        #refresh_token = create_refresh_token(identity='default')

        response = jsonify({
            'access_token': access_token,
            #'refresh_token': refresh_token,
        })
        #set_access_cookies(response, access_token)
    else:
        response = jsonify({
            'error': 'Unkown user or bad password',
        })
        response.status_code = 401
    return response
