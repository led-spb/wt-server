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
    def get_user_by_login(cls, login :str) -> User|None:
        return db.session.execute(
            db.select(User).filter(User.login == login)
        ).scalar_one_or_none()
    
    @classmethod
    def register_user(cls, login :str, password :str, invite :str|None) -> User:
        new_user = User(login=login, name=login)
        new_user.set_password(password)
        db.session.add(new_user)
        
        if invite is not None:
            InvitesService.redeem_invite(invite, new_user)
        db.session.commit()
        return new_user
