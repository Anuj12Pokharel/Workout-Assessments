"""Workout recommendation endpoints"""
from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app import crud
from app.middleware import create_success_response

router = APIRouter(prefix="/api/v1/users", tags=["recommendations"])


@router.get("/{user_id}/recommendations", response_model=dict, status_code=status.HTTP_200_OK)
def get_workout_recommendation(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Get next recommended workout with context
    
    - **user_id**: User ID
    
    Returns recommendation based on past performance with context about:
    - Last workout details
    - Progression trend
    - Reasoning for the recommendation
    """
    recommendation_data = crud.get_recommendation(db, user_id)
    
    # Format response
    response_data = {
        "user_id": user_id,
        "recommended_reps": recommendation_data["recommended_reps"],
        "recommendation_reason": recommendation_data["reason"]
    }
    
    # Add last workout info if available
    if recommendation_data["last_session"]:
        last_session = recommendation_data["last_session"]
        response_data["last_workout"] = {
            "session_id": last_session.id,
            "assigned_reps": last_session.exercise.assigned_reps,
            "completed_reps": last_session.exercise.completed_reps,
            "date": last_session.ended_at or last_session.started_at
        }
    else:
        response_data["last_workout"] = None
    
    # Add progression info
    response_data["progression"] = recommendation_data["progression"]
    
    return create_success_response(
        data=response_data,
        request_id=getattr(request.state, "request_id", None)
    )
