from flask import Blueprint, request, current_app as app, jsonify
from marshmallow import Schema, fields
from ..services.invites import InvitesService

invites_view = Blueprint('invites', __name__)


@invites_view.route('/<string:invite>', methods=['GET'])
def validate_invite(invite):
    status = InvitesService.invite_is_valid(invite)
    return jsonify(dict(status=status, message='Invite is valid' if status else 'Invite is invalid')), 200
