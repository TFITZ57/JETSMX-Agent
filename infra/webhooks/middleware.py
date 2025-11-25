"""
Middleware for webhook receiver.
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import time
from shared.logging.logger import setup_logger

logger = setup_logger(__name__)


def setup_middleware(app: FastAPI):
    """Setup middleware for the FastAPI app."""
    
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Log all incoming requests."""
        start_time = time.time()
        
        logger.info(
            f"Incoming request: {request.method} {request.url.path}",
            extra={"extra_fields": {
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else None
            }}
        )
        
        response = await call_next(request)
        
        duration = time.time() - start_time
        logger.info(
            f"Request completed: {request.method} {request.url.path} - {response.status_code} ({duration:.3f}s)",
            extra={"extra_fields": {
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_seconds": duration
            }}
        )
        
        return response
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Handle uncaught exceptions."""
        logger.error(
            f"Unhandled exception: {str(exc)}",
            exc_info=True,
            extra={"extra_fields": {
                "path": request.url.path,
                "method": request.method
            }}
        )
        
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"}
        )

