"""Workout session management endpoints"""
import math
from datetime import datetime
from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app import crud, schemas
from app.middleware import create_success_response

router = APIRouter(prefix="/api/v1", tags=["workouts"])


@router.post("/users/{user_id}/workouts", response_model=dict, status_code=status.HTTP_201_CREATED)
def start_workout(
    user_id: int,
    workout: schemas.WorkoutSessionCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Start a new workout session for a user
    
    - **user_id**: User ID
    - **assigned_reps**: Target number of reps
    - **exercise_name**: Optional exercise name (default: Push-ups)
    """
    db_session = crud.create_workout_session(
        db,
        user_id=user_id,
        assigned_reps=workout.assigned_reps,
        exercise_name=workout.exercise_name or "Push-ups"
    )
    
    # Format response
    session_data = {
        "id": db_session.id,
        "user_id": db_session.user_id,
        "started_at": db_session.started_at,
        "ended_at": db_session.ended_at,
        "status": "active" if db_session.is_active else "completed",
        "exercise": {
            "assigned_reps": db_session.exercise.assigned_reps,
            "completed_reps": db_session.exercise.completed_reps,
            "exercise_name": db_session.exercise.exercise_name,
            "completion_percentage": None
        }
    }
    
    # Add HATEOAS links
    links = {
        "log": f"/api/v1/workouts/{db_session.id}/log",
        "end": f"/api/v1/workouts/{db_session.id}/end"
    }
    
    return create_success_response(
        data=session_data,
        links=links,
        request_id=getattr(request.state, "request_id", None)
    )


@router.get("/users/{user_id}/workouts", response_model=dict, status_code=status.HTTP_200_OK)
def list_user_workouts(
    user_id: int,
    request: Request,
    status_filter: str = "all",
    page: int = 1,
    limit: int = 20,
    sort_by: str = "started_at",
    order: str = "desc",
    db: Session = Depends(get_db)
):
    """
    Get workout history for a user
    
    - **user_id**: User ID
    - **status_filter**: Filter by status (active, completed, all)
    - **page**: Page number (default: 1)
    - **limit**: Items per page (default: 20, max: 100)
    - **sort_by**: Sort field
    - **order**: Sort order (asc, desc)
    """
    # Validate and limit page size
    limit = min(limit, 100)
    skip = (page - 1) * limit
    
    sessions, total = crud.get_user_workout_sessions(
        db,
        user_id=user_id,
        status=status_filter,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        order=order
    )
    
    # Format sessions
    sessions_data = [
        {
            "id": session.id,
            "user_id": session.user_id,
            "started_at": session.started_at,
            "ended_at": session.ended_at,
            "status": "active" if session.is_active else "completed",
            "exercise": {
                "assigned_reps": session.exercise.assigned_reps,
                "completed_reps": session.exercise.completed_reps,
                "exercise_name": session.exercise.exercise_name,
                "completion_percentage": (
                    round((session.exercise.completed_reps / session.exercise.assigned_reps) * 100, 2)
                    if session.exercise.completed_reps is not None and session.exercise.assigned_reps > 0
                    else None
                )
            }
        }
        for session in sessions
    ]
    
    # Calculate pagination metadata
    total_pages = math.ceil(total / limit) if total > 0 else 1
    
    return create_success_response(
        data=sessions_data,
        meta={
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_items": total,
                "items_per_page": limit
            }
        },
        request_id=getattr(request.state, "request_id", None)
    )


@router.get("/workouts/{session_id}", response_model=dict, status_code=status.HTTP_200_OK)
def get_workout_session(
    session_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Get specific workout session details
    
    - **session_id**: Workout session ID
    """
    session = crud.get_workout_session(db, session_id)
    
    # Format response
    session_data = {
        "id": session.id,
        "user_id": session.user_id,
        "started_at": session.started_at,
        "ended_at": session.ended_at,
        "status": "active" if session.is_active else "completed",
        "exercise": {
            "assigned_reps": session.exercise.assigned_reps,
            "completed_reps": session.exercise.completed_reps,
            "exercise_name": session.exercise.exercise_name,
            "completion_percentage": (
                round((session.exercise.completed_reps / session.exercise.assigned_reps) * 100, 2)
                if session.exercise.completed_reps is not None and session.exercise.assigned_reps > 0
                else None
            )
        }
    }
    
    return create_success_response(
        data=session_data,
        request_id=getattr(request.state, "request_id", None)
    )


@router.patch("/workouts/{session_id}/log", response_model=dict, status_code=status.HTTP_200_OK)
def log_exercise_result(
    session_id: int,
    exercise_log: schemas.ExerciseLog,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Log exercise result (reps completed)
    
    - **session_id**: Workout session ID
    - **completed_reps**: Number of reps completed (non-negative)
    """
    session = crud.log_exercise(db, session_id, exercise_log.completed_reps)
    
    # Calculate completion percentage
    completion_percentage = None
    if session.exercise.assigned_reps > 0:
        completion_percentage = round(
            (session.exercise.completed_reps / session.exercise.assigned_reps) * 100, 2
        )
    
    # Format response
    response_data = {
        "session_id": session.id,
        "exercise": {
            "assigned_reps": session.exercise.assigned_reps,
            "completed_reps": session.exercise.completed_reps,
            "completion_percentage": completion_percentage
        }
    }
    
    return create_success_response(
        data=response_data,
        message="Exercise logged successfully",
        request_id=getattr(request.state, "request_id", None)
    )


@router.patch("/workouts/{session_id}/end", response_model=dict, status_code=status.HTTP_200_OK)
def end_workout(
    session_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    End workout session and calculate recommendation
    
    - **session_id**: Workout session ID
    """
    session, next_reps = crud.end_workout_session(db, session_id)
    
    # Calculate duration
    duration_minutes = 0
    if session.ended_at and session.started_at:
        duration = session.ended_at - session.started_at
        duration_minutes = round(duration.total_seconds() / 60, 2)
    
    # Determine performance
    performance = "completed" if session.exercise.completed_reps >= session.exercise.assigned_reps else "incomplete"
    
    # Format response
    response_data = {
        "session_id": session.id,
        "ended_at": session.ended_at,
        "duration_minutes": duration_minutes,
        "summary": {
            "assigned_reps": session.exercise.assigned_reps,
            "completed_reps": session.exercise.completed_reps,
            "performance": performance,
            "next_recommended_reps": next_reps
        }
    }
    
    return create_success_response(
        data=response_data,
        message=f"Workout completed! Next workout: {next_reps} reps",
        request_id=getattr(request.state, "request_id", None)
    )
