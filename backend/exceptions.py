from http import HTTPStatus
from typing import Any, Optional


class ApiException(Exception):
    """Base exception for all API errors"""
    def __init__(
        self,
        message: str = "An unexpected error occurred",
        status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR,
        payload: Optional[Any] = None
    ):
        self.message = message
        self.status_code = status_code
        self.payload = payload
        super().__init__(self.message)


class ValidationException(ApiException):
    """Raised when request validation fails"""
    def __init__(
        self,
        message: str = "Validation error",
        payload: Optional[Any] = None
    ):
        super().__init__(
            message=message,
            status_code=HTTPStatus.BAD_REQUEST,
            payload=payload
        )


class UnauthorizedException(ApiException):
    """Raised when authentication fails"""
    def __init__(
        self,
        message: str = "Unauthorized access",
        payload: Optional[Any] = None
    ):
        super().__init__(
            message=message,
            status_code=HTTPStatus.UNAUTHORIZED,
            payload=payload
        )


class NotFoundException(ApiException):
    """Raised when a requested resource is not found"""
    def __init__(
        self,
        message: str = "Resource not found",
        payload: Optional[Any] = None
    ):
        super().__init__(
            message=message,
            status_code=HTTPStatus.NOT_FOUND,
            payload=payload
        )


class DuplicateResourceException(ApiException):
    """Raised when attempting to create a resource that already exists"""
    def __init__(
        self,
        message: str = "Resource already exists",
        payload: Optional[Any] = None
    ):
        super().__init__(
            message=message,
            status_code=HTTPStatus.CONFLICT,
            payload=payload
        )


# class ValidationError(Exception):
#     """Exception raised for validation errors."""
#     pass

# class NotFoundError(Exception):
#     """Exception raised when a resource is not found."""
#     pass

# class UnauthorizedError(Exception):
#     """Exception raised when a user is not authorized."""
#     pass