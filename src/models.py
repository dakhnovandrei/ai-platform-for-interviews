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

    interview_session = relationship('InterviewSessions', back_populates='user')


class InterviewSessions(Base):
    __tablename__ = "interview_sessions"

    interview_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.user_id'))
    job_position = Column(String(100), nullable=False)
    company = Column(String(100))
    interview_type = Column(String(50))
    created_at = Column(DateTime, default=datetime.datetime.utcnow())
    finished_at = Column(DateTime)
    status = Column(String(20), default='active')
    feedback = Column(Text)

    user = relationship('Users', back_populates='interview_session')
    message = relationship('Messages', back_populates='session')


class Messages(Base):
    __tablename__ = "messages"
    message_id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey('interview_sessions.interview_id'))
    content = Column(Text, nullable=False)
    is_user = Column(Boolean, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow())

    session = relationship('InterviewSessions', back_populates='message')
