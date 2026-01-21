"""SQLAlchemy database models"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    """User model - represents app users"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    workout_sessions = relationship("WorkoutSession", back_populates="user", cascade="all, delete-orphan")
    recommendation = relationship("WorkoutRecommendation", back_populates="user", uselist=False, cascade="all, delete-orphan")


class WorkoutSession(Base):
    """WorkoutSession model - represents individual workout sessions"""
    __tablename__ = "workout_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="workout_sessions")
    exercise = relationship("Exercise", back_populates="session", uselist=False, cascade="all, delete-orphan")


class Exercise(Base):
    """Exercise model - represents exercises performed in workout sessions"""
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("workout_sessions.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    exercise_name = Column(String(100), default="Push-ups", nullable=False)
    assigned_reps = Column(Integer, nullable=False)
    completed_reps = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    session = relationship("WorkoutSession", back_populates="exercise")


class WorkoutRecommendation(Base):
    """WorkoutRecommendation model - stores next recommended workout for users"""
    __tablename__ = "workout_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    next_recommended_reps = Column(Integer, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="recommendation")
