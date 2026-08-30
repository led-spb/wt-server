from ..models import db
from ..models.user import User
from .invites import InvitesService


class UserService:

    @classmethod
    def get_user_by_id(cls, id :int) -> User|None:
        return db.session.execute(
            db.select(User).filter(User.id == id)
        ).scalar_one_or_none()

    @classmethod
    def get_user_by_email(cls, email :str) -> User|None:
        return db.session.execute(
            db.select(User).filter(User.email == email)
        ).scalar_one_or_none()
    
    @classmethod
    def register_user(cls, email :str, name: str, password :str, invite :str|None) -> User:
        new_user = User(email=email, name=name)
        new_user.set_password(password)
        db.session.add(new_user)
        
        if invite is not None:
            InvitesService.redeem_invite(invite, new_user)
        db.session.commit()
        return new_user
