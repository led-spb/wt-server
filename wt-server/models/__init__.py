from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, nulls_first, desc
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    ...


db = SQLAlchemy(model_class=Base)
order_random = func.random
order_desc = desc
