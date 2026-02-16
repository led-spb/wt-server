import uuid
import os.path
from flask import Blueprint, request, current_app as app
from ..models import db
from ..models.user import UserReport
from ..services.users import UserService
from ..services.stats import UserStatService
from ..services.invites import InvitesService
from ..services.words import WordService
from datetime import date, datetime, timedelta
from marshmallow import Schema, fields, ValidationError, validate, missing
from flask_jwt_extended import jwt_required, current_user


users = Blueprint('users', __name__)

def name_validation(value):
    if str(value).strip() == '':
        raise ValidationError('Value must be not empty')
    if not (4 <= len(str(value).strip()) <= 16):
        raise ValidationError('Value length must be in range')

class UserSchema(Schema):
    id = fields.Int(required=True, dump_only=True)
    email = fields.Email(required=True)
    name = fields.Str(required=True, validate=name_validation)
    daily_goal = fields.Integer(data_key='dailyGoal')
    avatar_image = fields.String(data_key='avatar')

class UpdateUserSchema(Schema):
    name = fields.Str(validate=name_validation)
    daily_goal = fields.Integer(data_key='dailyGoal')

class RegisterUserSchema(Schema):
    invite = fields.String(required=True)
    email = fields.Email(required=True)
    name = fields.Str(required=True, validate=name_validation)
    password = fields.String(required=True)


@users.get('')
@jwt_required()
def get_user_info():
    return UserSchema().dump(current_user)

@users.put('')
@jwt_required()
def update_user_info():
    data = UpdateUserSchema().load(request.get_json())
    if data.get('name') is not None and data.get('name') != current_user:
        if current_user.updated_at is not None \
            and datetime.now() - current_user.updated_at < timedelta(days=7):
            raise ValidationError("Forbbiden to change name", field_name='name')
        current_user.name = data.get('name').strip()
        current_user.updated_at = datetime.now()
    if data.get('daily_goal') is not None:
        current_user.daily_goal = data.get('daily_goal')
    
    db.session.commit()
    return UserSchema().dump(current_user)

@users.post('/avatar')
@jwt_required()
def update_user_avatar():
    file = request.files.get('file')
    if file is None or file.filename == "":
        raise ValidationError("file is not provided")
    

    uniq_filename = str(uuid.uuid4())
    file.save(os.path.join(app.config.get('UPLOAD_DIR'), uniq_filename))

    current_user.avatar_image = uniq_filename
    db.session.commit()

    return UserSchema().dump(current_user)


@users.post('/register')
def register_user():
    data = RegisterUserSchema().load(request.get_json())

    if not InvitesService.invite_is_valid(data.get('invite')):
        raise ValidationError('Invite is invalid', field_name='invite')

    if UserService.get_user_by_email(email=data.get('email')) is not None:
        raise ValidationError('User is already exists', field_name='email')
    
    UserService.register_user(
        email=data.get('email'),
        name=data.get('name'),
        password=data.get('password'),
        invite=data.get('invite')
    )

    return '', 204

class GoalSchema(Schema):
    total = fields.Integer()
    learned = fields.Integer()

class UserProgressSchema(Schema):
    series = fields.Integer()
    overall = fields.Nested(GoalSchema)
    today = fields.Nested(GoalSchema)


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
