from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
import os


ABSOLUTE = os.getcwd() + os.sep
DATABASE = f'{ABSOLUTE}db.sqlite3'
URI = f"sqlite:///{DATABASE}"

engine = create_engine(URI)
db = scoped_session(sessionmaker(bind=engine, autocommit=False, autoflush=False))
Base = declarative_base()


class Users(Base):
        __tablename__ = "users"
        id = Column(Integer, primary_key=True)
        username = Column(String, nullable = False)
        password = Column(String, nullable = False)
        email = Column(String, nullable = False)

class Daily(Base):
        __tablename__ = "daily"
        id = Column(Integer, primary_key=True)
        user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
        timestamp = Column(String, nullable = False)
        weight = Column(Integer)
        calories = Column(Integer)
        steps = Column(Integer)

class Hourly(Base):
        __tablename__ = "hourly"
        id = Column(Integer, primary_key=True)
        user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
        timestamp = Column(String, nullable = False)
        blood_sugar = Column(Integer, nullable=False)
        symptoms = Column(String)
        # 0 = before meal, 1 = after meal
        meal_status = Column(Integer, nullable = False)
