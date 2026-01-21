"""Pydantic schemas for request/response validation"""
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field, EmailStr, field_validator


# ============= User Schemas =============

class UserCreate(BaseModel):
    """Schema for creating a new user"""
    name: str = Field(..., min_length=2, max_length=100, description="User's full name")
    email: Optional[EmailStr] = Field(None, description="User's email address")


class UserStats(BaseModel):
    """Schema for user statistics"""
    total_workouts: int
    total_exercises: int
    active_sessions: int
    current_recommended_reps: int


class UserResponse(BaseModel):
    """Schema for user response"""
    id: int
    name: str
    email: Optional[str]
    created_at: datetime
    total_workouts: Optional[int] = 0

    class Config:
        from_attributes = True


class UserDetailResponse(BaseModel):
    """Schema for detailed user response with stats"""
    id: int
    name: str
    email: Optional[str]
    created_at: datetime
    stats: UserStats

    class Config:
        from_attributes = True


# ============= Workout Session Schemas =============

class WorkoutSessionCreate(BaseModel):
    """Schema for creating a workout session"""
    assigned_reps: int = Field(..., gt=0, description="Target number of reps")
    exercise_name: Optional[str] = Field("Push-ups", max_length=100, description="Exercise name")


class ExerciseData(BaseModel):
    """Schema for exercise data within workout session"""
    assigned_reps: int
    completed_reps: Optional[int]
    exercise_name: str
    completion_percentage: Optional[float] = None

    class Config:
        from_attributes = True


class WorkoutSessionResponse(BaseModel):
    """Schema for workout session response"""
    id: int
    user_id: int
    started_at: datetime
    ended_at: Optional[datetime]
    status: str
    exercise: ExerciseData

    class Config:
        from_attributes = True


class WorkoutSessionLinks(BaseModel):
    """HATEOAS links for workout session"""
    log: str
    end: str


# ============= Exercise Schemas =============

class ExerciseLog(BaseModel):
    """Schema for logging exercise results"""
    completed_reps: int = Field(..., ge=0, description="Number of reps completed")


class ExerciseLogResponse(BaseModel):
    """Schema for exercise log response"""
    session_id: int
    exercise: ExerciseData


# ============= Workout Summary Schemas =============

class WorkoutSummary(BaseModel):
    """Schema for workout summary"""
    assigned_reps: int
    completed_reps: int
    performance: str
    next_recommended_reps: int


class WorkoutEndResponse(BaseModel):
    """Schema for workout end response"""
    session_id: int
    ended_at: datetime
    duration_minutes: float
    summary: WorkoutSummary


# ============= Recommendation Schemas =============

class LastWorkoutInfo(BaseModel):
    """Schema for last workout information"""
    session_id: int
    assigned_reps: int
    completed_reps: int
    date: datetime


class ProgressionInfo(BaseModel):
    """Schema for progression information"""
    trend: str
    total_increase: int
    sessions_count: int


class RecommendationResponse(BaseModel):
    """Schema for recommendation response"""
    user_id: int
    recommended_reps: int
    recommendation_reason: str
    last_workout: Optional[LastWorkoutInfo]
    progression: Optional[ProgressionInfo]


# ============= API Response Envelope =============

class PaginationMeta(BaseModel):
    """Schema for pagination metadata"""
    current_page: int
    total_pages: int
    total_items: int
    items_per_page: int


class ResponseMeta(BaseModel):
    """Schema for response metadata"""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None
    pagination: Optional[PaginationMeta] = None


class ErrorDetail(BaseModel):
    """Schema for error details"""
    code: str
    message: str
    field: Optional[str] = None


class APIResponse(BaseModel):
    """Standard API response envelope"""
    success: bool
    data: Optional[Any] = None
    errors: Optional[list[ErrorDetail]] = None
    meta: ResponseMeta
    message: Optional[str] = None
    links: Optional[dict] = None
