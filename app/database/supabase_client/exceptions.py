"""
Custom exceptions for Supabase client operations
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

class SupabaseError(Exception):
    """Base class for all Supabase-related errors"""
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error
        logger.error(f"SupabaseError: {message}", exc_info=original_error)

class AuthenticationError(SupabaseError):
    """Raised when authentication fails"""
    def __init__(self, message: str = "Authentication failed", original_error: Optional[Exception] = None):
        super().__init__(message, original_error)

class APIError(SupabaseError):
    """Raised when the Supabase API returns an error"""
    def __init__(self, message: str, status_code: int = None, original_error: Optional[Exception] = None):
        self.status_code = status_code
        super().__init__(message, original_error)

class BadRequestError(APIError):
    """Raised when the request is invalid"""
    def __init__(self, message: str = "Bad request", original_error: Optional[Exception] = None):
        super().__init__(message, 400, original_error)

class NotFoundError(APIError):
    """Raised when a resource is not found"""
    def __init__(self, message: str = "Resource not found", original_error: Optional[Exception] = None):
        super().__init__(message, 404, original_error)

class ConflictError(APIError):
    """Raised when a conflict occurs (e.g., duplicate entry)"""
    def __init__(self, message: str = "Conflict", original_error: Optional[Exception] = None):
        super().__init__(message, 409, original_error)

class InternalServerError(APIError):
    """Raised when the server encounters an error"""
    def __init__(self, message: str = "Internal server error", original_error: Optional[Exception] = None):
        super().__init__(message, 500, original_error)

class ServiceUnavailableError(APIError):
    """Raised when the service is unavailable"""
    def __init__(self, message: str = "Service unavailable", original_error: Optional[Exception] = None):
        super().__init__(message, 503, original_error)

class TimeoutError(SupabaseError):
    """Raised when a request times out"""
    def __init__(self, message: str = "Request timed out", original_error: Optional[Exception] = None):
        super().__init__(message, original_error)

class StorageError(SupabaseError):
    """Base class for storage-related errors"""
    def __init__(self, message: str, bucket: Optional[str] = None, original_error: Optional[Exception] = None):
        self.bucket = bucket
        super().__init__(message, original_error)

class BucketNotFoundError(StorageError):
    """Raised when a storage bucket is not found"""
    def __init__(self, bucket: str, original_error: Optional[Exception] = None):
        super().__init__(f"Bucket not found: {bucket}", bucket, original_error)

class StorageUploadError(StorageError):
    """Raised when a file upload fails"""
    def __init__(self, message: str, bucket: str, file_path: str, original_error: Optional[Exception] = None):
        self.file_path = file_path
        super().__init__(message, bucket, original_error)

class StorageDownloadError(StorageError):
    """Raised when a file download fails"""
    def __init__(self, message: str, bucket: str, file_path: str, original_error: Optional[Exception] = None):
        self.file_path = file_path
        super().__init__(message, bucket, original_error)

class ValidationError(SupabaseError):
    """Raised when data validation fails"""
    def __init__(self, message: str, data: Optional[dict] = None, original_error: Optional[Exception] = None):
        self.data = data
        super().__init__(message, original_error)

class ConnectionError(SupabaseError):
    """Raised when there's a connection issue"""
    def __init__(self, message: str = "Connection error", original_error: Optional[Exception] = None):
        super().__init__(message, original_error)

class RateLimitError(SupabaseError):
    """Raised when rate limit is exceeded"""
    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None, original_error: Optional[Exception] = None):
        self.retry_after = retry_after
        super().__init__(message, original_error)

class PermissionError(SupabaseError):
    """Raised when there's a permission issue"""
    def __init__(self, message: str = "Permission denied", original_error: Optional[Exception] = None):
        super().__init__(message, original_error)

class RetryableError(SupabaseError):
    """Base class for errors that might be resolved by retrying"""
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message, original_error)

class NonRetryableError(SupabaseError):
    """Base class for errors that should not be retried"""
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message, original_error)

class ForbiddenError(NonRetryableError):
    """Raised when a request is forbidden"""
    def __init__(self, message: str = "Forbidden", original_error: Optional[Exception] = None):
        super().__init__(message, original_error)

class GatewayTimeoutError(NonRetryableError):
    """Raised when a gateway timeout occurs"""
    def __init__(self, message: str = "Gateway timeout", original_error: Optional[Exception] = None):
        super().__init__(message, original_error)

class UnauthorizedError(NonRetryableError):
    """Raised when a request is unauthorized"""
    def __init__(self, message: str = "Unauthorized", original_error: Optional[Exception] = None):
        super().__init__(message, original_error)

class TooManyRequestsError(NonRetryableError):
    """Raised when too many requests are made"""
    def __init__(self, message: str = "Too many requests", original_error: Optional[Exception] = None):
        super().__init__(message, original_error)

__all__ = [
    "SupabaseError",
    "AuthenticationError",
    "APIError",
    "BadRequestError",
    "NotFoundError",
    "ConflictError",
    "InternalServerError",
    "ServiceUnavailableError",
    "TimeoutError",
    "StorageError",
    "BucketNotFoundError",
    "StorageUploadError",
    "StorageDownloadError",
    "ValidationError",
    "ConnectionError",
    "RateLimitError",
    "PermissionError",
    "RetryableError",
    "NonRetryableError",
    "ForbiddenError",
    "GatewayTimeoutError",
    "UnauthorizedError",
    "TooManyRequestsError",
    "InternalServerError",
    "ServiceUnavailableError",
]
