# app/exceptions.py

from fastapi import Request
from fastapi.responses import JSONResponse


class DatabaseConnectionError(Exception):
    """Raised when the database connection pool fails to initialize."""
    pass


class ContactNotFoundError(Exception):
    """Raised when a contact lookup returns no results unexpectedly."""
    pass


class InvalidRequestError(Exception):
    """Raised when request data fails business logic validation."""
    pass


# ─── Handlers ───────────────────────────────────────────────────────────────

async def database_connection_error_handler(request: Request, exc: DatabaseConnectionError):
    return JSONResponse(
        status_code=503,
        content={
            "error": "Service Unavailable",
            "message": "Database connection failed. Please try again later."
        }
    )


async def contact_not_found_error_handler(request: Request, exc: ContactNotFoundError):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": str(exc)
        }
    )


async def invalid_request_error_handler(request: Request, exc: InvalidRequestError):
    return JSONResponse(
        status_code=400,
        content={
            "error": "Bad Request",
            "message": str(exc)
        }
    )