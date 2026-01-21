"""Custom exception classes for the API"""
from fastapi import HTTPException, status


class UserNotFoundException(HTTPException):
    """Exception raised when a user is not found"""
    def __init__(self, user_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "USER_NOT_FOUND",
                "message": f"User with ID {user_id} does not exist",
                "field": "user_id"
            }
        )


class WorkoutSessionNotFoundException(HTTPException):
    """Exception raised when a workout session is not found"""
    def __init__(self, session_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "WORKOUT_SESSION_NOT_FOUND",
                "message": f"Workout session with ID {session_id} does not exist",
                "field": "session_id"
            }
        )


class ActiveSessionExistsException(HTTPException):
    """Exception raised when user tries to start a new session while one is active"""
    def __init__(self, user_id: int, active_session_id: int):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "ACTIVE_SESSION_EXISTS",
                "message": f"User {user_id} already has an active workout session (ID: {active_session_id})",
                "field": "user_id",
                "active_session_id": active_session_id
            }
        )


class SessionNotActiveException(HTTPException):
    """Exception raised when trying to perform operations on an inactive session"""
    def __init__(self, session_id: int):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "SESSION_NOT_ACTIVE",
                "message": f"Workout session {session_id} is not active",
                "field": "session_id"
            }
        )


class ExerciseNotLoggedException(HTTPException):
    """Exception raised when trying to end a session without logging exercise"""
    def __init__(self, session_id: int):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "EXERCISE_NOT_LOGGED",
                "message": f"Cannot end session {session_id}: exercise results not logged",
                "field": "session_id"
            }
        )


class ValidationException(HTTPException):
    """Exception raised for validation errors"""
    def __init__(self, message: str, field: str = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "VALIDATION_ERROR",
                "message": message,
                "field": field
            }
        )
