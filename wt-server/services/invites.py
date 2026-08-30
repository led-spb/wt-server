from ..models import db
from ..models.user import User, Invite
from datetime import datetime


class InvitesService:

    @classmethod
    def invite_is_valid(cls, invite_hash: str) -> bool:
        invite = db.session.execute(
            db.select(
                Invite
            ).filter(
                Invite.hash == invite_hash
            )
        ).scalar_one_or_none()

        return invite is not None \
            and invite.registered_user_id is None \
            and invite.lifetime > datetime.now()

    @classmethod
    def redeem_invite(cls, invite_hash: str, user :User) -> None:
        invite = db.session.execute(
            db.select(
                Invite
            ).filter(
                Invite.hash == invite_hash
            )
        ).scalar_one_or_none()
        if invite is None:
            return
        invite.registered_user = user
        db.session.add(invite)
        db.session.commit()
