"""User management endpoints"""
import math
from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import crud, schemas
from app.middleware import create_success_response

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_user(
    user: schemas.UserCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Create a new user
    
    - **name**: User's full name (2-100 characters)
    - **email**: Optional email address
    """
    db_user = crud.create_user(db, name=user.name, email=user.email)
    
    # Get total workouts for response
    user_data = {
        "id": db_user.id,
        "name": db_user.name,
        "email": db_user.email,
        "created_at": db_user.created_at,
        "total_workouts": 0
    }
    
    return create_success_response(
        data=user_data,
        request_id=getattr(request.state, "request_id", None)
    )


@router.get("/{user_id}", response_model=dict, status_code=status.HTTP_200_OK)
def get_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Get user details with workout statistics
    
    - **user_id**: User ID
    """
    db_user = crud.get_user(db, user_id)
    stats = crud.get_user_stats(db, user_id)
    
    user_data = {
        "id": db_user.id,
        "name": db_user.name,
        "email": db_user.email,
        "created_at": db_user.created_at,
        "stats": stats
    }
    
    return create_success_response(
        data=user_data,
        request_id=getattr(request.state, "request_id", None)
    )


@router.get("", response_model=dict, status_code=status.HTTP_200_OK)
def list_users(
    request: Request,
    page: int = 1,
    limit: int = 20,
    sort_by: str = "created_at",
    order: str = "desc",
    db: Session = Depends(get_db)
):
    """
    List all users with pagination
    
    - **page**: Page number (default: 1)
    - **limit**: Items per page (default: 20, max: 100)
    - **sort_by**: Sort field (created_at, name)
    - **order**: Sort order (asc, desc)
    """
    # Validate and limit page size
    limit = min(limit, 100)
    skip = (page - 1) * limit
    
    users, total = crud.get_users(db, skip=skip, limit=limit, sort_by=sort_by, order=order)
    
    # Format users
    users_data = [
        {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "created_at": user.created_at,
            "total_workouts": len(user.workout_sessions)
        }
        for user in users
    ]
    
    # Calculate pagination metadata
    total_pages = math.ceil(total / limit) if total > 0 else 1
    
    return create_success_response(
        data=users_data,
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
