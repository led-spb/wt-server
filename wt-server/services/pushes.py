from ..models import db
from ..models.user import User, WebPushSubscription
from datetime import datetime
import json


class WebPushService:

    @classmethod
    def register_web_push(cls, user :User, subscription_info :dict) -> WebPushSubscription:
        subscription = cls.find_web_push(user, subscription_info)
        if subscription is None:
            subscription = WebPushSubscription(
                user=user,
                endpoint=subscription_info.get('endpoint'),
                push_info=json.dumps(subscription_info)
            )
        subscription.create_at = datetime.now()
        db.session.add(subscription)
        db.session.commit()

        return subscription
    
    @classmethod
    def unregister_web_push(cls, user :User, subscription_info :dict) -> None:
        subscription = cls.find_web_push(user, subscription_info)
        if subscription is not None:
            db.session.delete(subscription)
            db.session.commit()
        pass

    @classmethod
    def find_web_push(cls, user :User, subscription_info :dict) -> WebPushSubscription|None:
        endpoint = subscription_info.get('endpoint')

        query = db.select(
            WebPushSubscription
        ).filter(
            WebPushSubscription.user == user
        ).filter(
            WebPushSubscription.endpoint == endpoint
        )
        return db.session.execute(query).scalar_one_or_none()
