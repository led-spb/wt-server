from flask import Blueprint, jsonify, request, current_app as app
from ..models import db
from ..models.user import User, UserReport
from ..services.users import UserService, UserStatService
from ..services.invites import InvitesService
from ..services.words import WordService
from datetime import date, timedelta
from marshmallow import Schema, fields, ValidationError, validate
from flask_jwt_extended import jwt_required, current_user


users = Blueprint('users', __name__)

class UserSchema(Schema):
    id = fields.Int(required=True, dump_only=True)
    login = fields.Str(required=True)
    name = fields.Str(required=True)
    daily_goal = fields.Integer()


@users.get('')
@jwt_required()
def get_user_info():
    return UserSchema().dump(current_user)

class AccentSchema(Schema):
    position = fields.Int()

class SpellingSchema(Schema):
    position = fields.Int()
    length = fields.Int()
    variants = fields.List(fields.String())

class WordSchema(Schema):
    id = fields.Int(dump_only=True, required=True)
    fullword = fields.Str(required=True)
    context = fields.Str()
    description = fields.Str()
    level = fields.Int(required=True)
    spellings = fields.Nested(SpellingSchema, many=True)
    accents = fields.Pluck(AccentSchema, 'position', many=True)

class StatisticSchema(Schema):
    success = fields.Int()
    failed = fields.Int()
    total = fields.Method("get_total")
    precent = fields.Method("get_precent")

    def get_total(self, obj):
        return obj.success + obj.failed

    def get_precent(self, obj):
        return obj.success / self.get_total(obj)

class WordStatSchema(StatisticSchema):
    word = fields.Nested(WordSchema)

class DayStatSchema(StatisticSchema):
    recorded_at = fields.Date()


class GoalSchema(Schema):
    total = fields.Integer()
    learned = fields.Integer()

class UserProgressSchema(Schema):
    series = fields.Integer()
    overall = fields.Nested(GoalSchema)
    today = fields.Nested(GoalSchema)

class UpdateUserStateSchema(Schema):
    failed = fields.List(fields.Int)
    success = fields.List(fields.Int)


@users.get('/progress')
@jwt_required()
def get_user_progress():
    stats = UserStatService.get_user_stats(current_user)

    series = 0
    today_progress = 0

    user_daily_goal = current_user.daily_goal

    now = date.today() - timedelta(days=1)
    for item in stats:
        if item.recorded_at == date.today():
            today_progress = item.success + item.failed
            continue
        if item.success + item.failed < user_daily_goal or item.recorded_at != now:
            break
        series += 1
        now -= timedelta(days=1)
    series += 1 if today_progress >= user_daily_goal else 0

    result = {
        'series': series,
        'overall': {
            'learned': UserStatService.get_user_progress(current_user),
            'total': WordService.get_total_words_count()
        },
        'today': {
            'learned': today_progress,
            'total': user_daily_goal,
        }
    }
    return UserProgressSchema().dump(result)


@users.get('/troubles')
@jwt_required()
def get_user_troubles():
    failed_words = UserStatService.get_user_word_failed(current_user, count=10)
    return WordStatSchema().dump(failed_words, many=True)

@users.get('/stat')
@jwt_required()
def get_user_stat():
    stats = UserStatService.get_user_stats(current_user, days=14)
    return DayStatSchema().dump(stats, many=True)


class UserRatingSchema(Schema):
    user = fields.Nested(UserSchema)
    success = fields.Integer()
    failed = fields.Integer()
    total = fields.Integer()
    progress = fields.Integer()
    progress_pct = fields.Float()

@users.get('/rating')
@jwt_required()
def get_rating():
    days = min(request.args.get('days', 7, type=int), 90)
    count = min(request.args.get('count', 5, type=int), 10)

    stat = UserStatService.get_users_with_aggregate_stat(days=days, count=count)
    total_words = WordService.get_total_words_count()

    return UserRatingSchema().dump(
        [
            dict(
                user=user,
                success=success,
                failed=failed,
                total=total,
                progress=progress,
                progress_pct=progress/total_words,
            )
            for (user, success, failed, total, progress, ) in stat
        ],
        many=True
    )

@users.put('/stat')
@jwt_required()
def update_user_stat():
    data = UpdateUserStateSchema().load(
        request.get_json()
    )
    UserStatService.update_user_stat(
        current_user,
        success=data.get('success', []),
        failed=data.get('failed', [])
    )
    return '', 204

class UserReportSchema(Schema):
    word = fields.Int(required=True)

@users.put('/report')
@jwt_required()
def put_user_report():
    data = UserReportSchema().load(
        request.get_json()
    )

    if current_user.reports is None:
        current_user.reports = UserReport(user_id=current_user.id, reports=[])

    report = current_user.reports
    report.reports = list(set(report.reports + [data.get('word')]))

    db.session.add(current_user)
    db.session.commit()

    return '', 204



class RegisterUserSchema(Schema):
    invite = fields.String(required=True)
    login = fields.String(required=True, validate=validate.Regexp(r'^[a-zA-Z][a-zA-Z0-9_]{3,}$'))
    password = fields.String(required=True)

@users.post('/register')
def register_user():
    data = RegisterUserSchema().load(request.get_json())

    if not InvitesService.invite_is_valid(data.get('invite')):
        raise ValidationError('Invite is invalid', field_name='invite')

    if UserService.get_user_by_login(data.get('login')) is not None:
        raise ValidationError('User is already exists', field_name='login')
    
    UserService.register_user(
        login=data.get('login'),
        password=data.get('password'),
        invite=data.get('invite')
    )

    return '', 204
