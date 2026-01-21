"""FastAPI application entry point"""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from datetime import datetime

from app.database import init_db
from app.middleware import RequestIDMiddleware, TimingMiddleware, create_error_response
from app.routers import users, workouts, recommendations

# Create FastAPI app
app = FastAPI(
    title="Workout Tracking API",
    description="Backend API for logging workout sessions and receiving personalized workout recommendations",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add middleware
app.add_middleware(RequestIDMiddleware)
app.add_middleware(TimingMiddleware)

# Include routers
app.include_router(users.router)
app.include_router(workouts.router)
app.include_router(recommendations.router)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors"""
    errors = []
    for error in exc.errors():
        errors.append({
            "code": "VALIDATION_ERROR",
            "message": error["msg"],
            "field": ".".join(str(x) for x in error["loc"])
        })
    
    return create_error_response(
        success=False,
        errors=errors,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        request_id=getattr(request.state, "request_id", None)
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    # If it's an HTTPException with detail as dict, use that
    if hasattr(exc, "status_code") and hasattr(exc, "detail"):
        if isinstance(exc.detail, dict):
            errors = [exc.detail]
        else:
            errors = [{
                "code": "ERROR",
                "message": str(exc.detail)
            }]
        
        return create_error_response(
            success=False,
            errors=errors,
            status_code=exc.status_code,
            request_id=getattr(request.state, "request_id", None)
        )
    
    # Generic error
    errors = [{
        "code": "INTERNAL_SERVER_ERROR",
        "message": "An unexpected error occurred"
    }]
    
    return create_error_response(
        success=False,
        errors=errors,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        request_id=getattr(request.state, "request_id", None)
    )


# Startup event
@app.on_event("startup")
def on_startup():
    """Initialize database on startup"""
    init_db()
    print("Database initialized successfully")


# Root endpoint
@app.get("/", response_model=dict, tags=["health"])
def read_root(request: Request):
    """API health check and information"""
    from app.middleware import create_success_response
    
    return create_success_response(
        data={
            "name": "Workout Tracking API",
            "version": "1.0.0",
            "status": "running",
            "documentation": "/docs"
        },
        request_id=getattr(request.state, "request_id", None)
    )


# Health check endpoint
@app.get("/health", response_model=dict, tags=["health"])
def health_check(request: Request):
    """Detailed health check"""
    from app.middleware import create_success_response
    
    return create_success_response(
        data={
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        },
        request_id=getattr(request.state, "request_id", None)
    )
