"""Middleware for request tracking and error handling"""
import uuid
import time
from datetime import datetime
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add unique request ID to each request"""
    
    async def dispatch(self, request: Request, call_next):
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Add request ID to response headers
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response


class TimingMiddleware(BaseHTTPMiddleware):
    """Middleware to track request processing time"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        return response


def create_error_response(
    success: bool,
    errors: list,
    status_code: int,
    request_id: str = None
) -> JSONResponse:
    """
    Create standardized error response
    
    Args:
        success: Whether the request was successful
        errors: List of error details
        status_code: HTTP status code
        request_id: Unique request identifier
    
    Returns:
        JSONResponse with standardized error format
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "success": success,
            "data": None,
            "errors": errors,
            "meta": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "request_id": request_id
            }
        }
    )


def create_success_response(
    data: any,
    message: str = None,
    links: dict = None,
    meta: dict = None,
    request_id: str = None
) -> dict:
    """
    Create standardized success response
    
    Args:
        data: Response data
        message: Optional success message
        links: Optional HATEOAS links
        meta: Optional additional metadata
        request_id: Unique request identifier
    
    Returns:
        Standardized response dictionary
    """
    response_meta = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "request_id": request_id
    }
    
    # Add additional metadata if provided
    if meta:
        response_meta.update(meta)
    
    response = {
        "success": True,
        "data": data,
        "errors": None,
        "meta": response_meta
    }
    
    if message:
        response["message"] = message
    
    if links:
        response["links"] = links
    
    return response
