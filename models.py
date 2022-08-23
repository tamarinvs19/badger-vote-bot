from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime
from sqlalchemy import create_engine
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from datetime import datetime


Base = declarative_base()


class Suggestion(Base):
    __tablename__ = 'suggestions'
    pk: int = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    text: str = Column(String(127))
    voter_count: int = Column(Integer)
    creator_id: int = Column(Integer)
    created_at: datetime.date = Column(DateTime)


class Vote(Base):
    __tablename__ = 'votes'
    pk: int = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    user_id: int = Column(Integer)
    suggestion_id: int = Column(Integer)
