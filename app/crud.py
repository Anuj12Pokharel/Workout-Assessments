"""CRUD operations for database models"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, asc

from app import models
from app.exceptions import (
    UserNotFoundException,
    WorkoutSessionNotFoundException,
    ActiveSessionExistsException,
    SessionNotActiveException,
    ExerciseNotLoggedException
)


# ============= Helper Functions =============

def calculate_next_reps(assigned_reps: int, completed_reps: int) -> int:
    """
    Calculate next recommended reps based on performance
    
    Rules:
    - If completed >= assigned: next = current + 2
    - If completed < assigned: next = current - 1
    - Minimum reps = 1
    
    Args:
        assigned_reps: Target reps
        completed_reps: Actual reps completed
    
    Returns:
        Next recommended reps (minimum 1)
    """
    if completed_reps >= assigned_reps:
        next_reps = assigned_reps + 2
    else:
        next_reps = assigned_reps - 1
    
    return max(1, next_reps)


# ============= User CRUD =============

def create_user(db: Session, name: str, email: Optional[str] = None) -> models.User:
    """Create a new user"""
    db_user = models.User(name=name, email=email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user(db: Session, user_id: int) -> models.User:
    """Get user by ID, raises exception if not found"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise UserNotFoundException(user_id)
    return user


def get_users(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    sort_by: str = "created_at",
    order: str = "desc"
) -> tuple[List[models.User], int]:
    """Get list of users with pagination"""
    query = db.query(models.User)
    
    # Get total count
    total = query.count()
    
    # Apply sorting
    sort_column = getattr(models.User, sort_by, models.User.created_at)
    if order == "asc":
        query = query.order_by(asc(sort_column))
    else:
        query = query.order_by(desc(sort_column))
    
    # Apply pagination
    users = query.offset(skip).limit(limit).all()
    
    return users, total


def get_user_stats(db: Session, user_id: int) -> dict:
    """Get user statistics"""
    user = get_user(db, user_id)
    
    total_workouts = db.query(models.WorkoutSession).filter(
        models.WorkoutSession.user_id == user_id
    ).count()
    
    total_exercises = db.query(models.Exercise).join(models.WorkoutSession).filter(
        models.WorkoutSession.user_id == user_id
    ).count()
    
    active_sessions = db.query(models.WorkoutSession).filter(
        models.WorkoutSession.user_id == user_id,
        models.WorkoutSession.is_active == True
    ).count()
    
    # Get current recommendation
    recommendation = db.query(models.WorkoutRecommendation).filter(
        models.WorkoutRecommendation.user_id == user_id
    ).first()
    
    current_recommended_reps = recommendation.next_recommended_reps if recommendation else 10
    
    return {
        "total_workouts": total_workouts,
        "total_exercises": total_exercises,
        "active_sessions": active_sessions,
        "current_recommended_reps": current_recommended_reps
    }


# ============= Workout Session CRUD =============

def create_workout_session(
    db: Session,
    user_id: int,
    assigned_reps: int,
    exercise_name: str = "Push-ups"
) -> models.WorkoutSession:
    """Create a new workout session"""
    # Verify user exists
    user = get_user(db, user_id)
    
    # Check for active session
    active_session = db.query(models.WorkoutSession).filter(
        models.WorkoutSession.user_id == user_id,
        models.WorkoutSession.is_active == True
    ).first()
    
    if active_session:
        raise ActiveSessionExistsException(user_id, active_session.id)
    
    # Create session
    db_session = models.WorkoutSession(user_id=user_id)
    db.add(db_session)
    db.flush()  # Get session ID without committing
    
    # Create exercise
    db_exercise = models.Exercise(
        session_id=db_session.id,
        assigned_reps=assigned_reps,
        exercise_name=exercise_name
    )
    db.add(db_exercise)
    
    db.commit()
    db.refresh(db_session)
    
    return db_session


def get_workout_session(db: Session, session_id: int) -> models.WorkoutSession:
    """Get workout session by ID"""
    session = db.query(models.WorkoutSession).options(
        joinedload(models.WorkoutSession.exercise),
        joinedload(models.WorkoutSession.user)
    ).filter(models.WorkoutSession.id == session_id).first()
    
    if not session:
        raise WorkoutSessionNotFoundException(session_id)
    
    return session


def get_user_workout_sessions(
    db: Session,
    user_id: int,
    status: str = "all",
    skip: int = 0,
    limit: int = 20,
    sort_by: str = "started_at",
    order: str = "desc"
) -> tuple[List[models.WorkoutSession], int]:
    """Get workout sessions for a user"""
    # Verify user exists
    get_user(db, user_id)
    
    query = db.query(models.WorkoutSession).options(
        joinedload(models.WorkoutSession.exercise)
    ).filter(models.WorkoutSession.user_id == user_id)
    
    # Filter by status
    if status == "active":
        query = query.filter(models.WorkoutSession.is_active == True)
    elif status == "completed":
        query = query.filter(models.WorkoutSession.is_active == False)
    
    # Get total count
    total = query.count()
    
    # Apply sorting
    sort_column = getattr(models.WorkoutSession, sort_by, models.WorkoutSession.started_at)
    if order == "asc":
        query = query.order_by(asc(sort_column))
    else:
        query = query.order_by(desc(sort_column))
    
    # Apply pagination
    sessions = query.offset(skip).limit(limit).all()
    
    return sessions, total


def log_exercise(db: Session, session_id: int, completed_reps: int) -> models.WorkoutSession:
    """Log exercise results for a workout session"""
    session = get_workout_session(db, session_id)
    
    if not session.is_active:
        raise SessionNotActiveException(session_id)
    
    # Update exercise
    session.exercise.completed_reps = completed_reps
    
    db.commit()
    db.refresh(session)
    
    return session


def end_workout_session(db: Session, session_id: int) -> tuple[models.WorkoutSession, int]:
    """End a workout session and calculate recommendation"""
    session = get_workout_session(db, session_id)
    
    if not session.is_active:
        raise SessionNotActiveException(session_id)
    
    # Check if exercise was logged
    if session.exercise.completed_reps is None:
        raise ExerciseNotLoggedException(session_id)
    
    # End session
    session.ended_at = datetime.utcnow()
    session.is_active = False
    
    # Calculate next recommendation
    next_reps = calculate_next_reps(
        session.exercise.assigned_reps,
        session.exercise.completed_reps
    )
    
    # Update or create recommendation
    recommendation = db.query(models.WorkoutRecommendation).filter(
        models.WorkoutRecommendation.user_id == session.user_id
    ).first()
    
    if recommendation:
        recommendation.next_recommended_reps = next_reps
        recommendation.updated_at = datetime.utcnow()
    else:
        recommendation = models.WorkoutRecommendation(
            user_id=session.user_id,
            next_recommended_reps=next_reps
        )
        db.add(recommendation)
    
    db.commit()
    db.refresh(session)
    
    return session, next_reps


# ============= Recommendation CRUD =============

def get_recommendation(db: Session, user_id: int) -> dict:
    """Get workout recommendation for a user"""
    # Verify user exists
    get_user(db, user_id)
    
    # Get recommendation
    recommendation = db.query(models.WorkoutRecommendation).filter(
        models.WorkoutRecommendation.user_id == user_id
    ).first()
    
    # Get last workout
    last_session = db.query(models.WorkoutSession).options(
        joinedload(models.WorkoutSession.exercise)
    ).filter(
        models.WorkoutSession.user_id == user_id,
        models.WorkoutSession.is_active == False
    ).order_by(desc(models.WorkoutSession.ended_at)).first()
    
    # Calculate progression
    completed_sessions = db.query(models.WorkoutSession).filter(
        models.WorkoutSession.user_id == user_id,
        models.WorkoutSession.is_active == False
    ).count()
    
    if recommendation:
        recommended_reps = recommendation.next_recommended_reps
    elif last_session and last_session.exercise:
        # Calculate from last session if no recommendation exists
        recommended_reps = calculate_next_reps(
            last_session.exercise.assigned_reps,
            last_session.exercise.completed_reps
        )
    else:
        # Default for new users
        recommended_reps = 10
    
    # Determine reason
    if last_session and last_session.exercise:
        if last_session.exercise.completed_reps >= last_session.exercise.assigned_reps:
            reason = "Completed all reps in last session"
            trend = "improving"
        else:
            reason = "Did not complete all reps in last session"
            trend = "adjusting"
    else:
        reason = "Starting recommendation"
        trend = "new"
    
    # Calculate total increase
    first_session = db.query(models.WorkoutSession).options(
        joinedload(models.WorkoutSession.exercise)
    ).filter(
        models.WorkoutSession.user_id == user_id,
        models.WorkoutSession.is_active == False
    ).order_by(asc(models.WorkoutSession.started_at)).first()
    
    total_increase = 0
    if first_session and first_session.exercise:
        total_increase = recommended_reps - first_session.exercise.assigned_reps
    
    return {
        "recommended_reps": recommended_reps,
        "reason": reason,
        "last_session": last_session,
        "progression": {
            "trend": trend,
            "total_increase": total_increase,
            "sessions_count": completed_sessions
        }
    }
