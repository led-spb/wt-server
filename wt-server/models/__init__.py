from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, nulls_first
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    ...


db = SQLAlchemy(model_class=Base)
order_random = func.random()
