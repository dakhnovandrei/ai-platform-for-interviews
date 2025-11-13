from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy import Column, Integer, String, Enum, Boolean, DateTime, JSON, ForeignKey, Float, Text
import datetime

Base = declarative_base()


class Users(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50))
    email = Column(String(100), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    subscription_type = Column(String(50), nullable=False, default="Base")
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
