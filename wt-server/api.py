import flask
from marshmallow.exceptions import ValidationError
from .views import *
from flask_jwt_extended import JWTManager


def create_api(app: flask.Flask) -> flask.Flask:
    jwt = JWTManager(app)

    @jwt.user_identity_loader
    def identity_loader(user):
        return user_identity_lookup(user)
    
    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        identity = jwt_data["sub"]
        return user_lookup(identity)

    @app.errorhandler(ValidationError)
    def on_validation_error(e):
        return flask.jsonify({'code': 'ValidationError', 'messages':e.messages}), 400

    app.register_blueprint(auth_view, url_prefix='/api/auth')
    app.register_blueprint(users_view, url_prefix='/api/user')
    app.register_blueprint(pushes_view, url_prefix='/api/user/push')
    app.register_blueprint(stats_view, url_prefix='/api/user/stat')

    app.register_blueprint(spellings_view, url_prefix='/api/spellings')
    app.register_blueprint(accents_view, url_prefix='/api/accents')
    app.register_blueprint(invites_view, url_prefix='/api/invites')
    app.register_blueprint(rules_view, url_prefix='/api/rules')
    app.register_blueprint(words_view, url_prefix='/api/words')

    # deprecated api, need to use /api/topics
    app.register_blueprint(topics_view, url_prefix='/api/tags')
    return app
