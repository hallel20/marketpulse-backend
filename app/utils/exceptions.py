"""
Custom exceptions for MarketPulse Commerce API
"""


class BaseException(Exception):
    """Base exception class"""
    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(self.detail)


class ValidationException(BaseException):
    """Raised when validation fails"""
    pass


class NotFoundException(BaseException):
    """Raised when resource is not found"""
    pass


class UnauthorizedException(BaseException):
    """Raised when user is not authorized"""
    pass


class ForbiddenException(BaseException):
    """Raised when user doesn't have permission"""
    pass


class PaymentException(BaseException):
    """Raised when payment processing fails"""
    pass


class InventoryException(BaseException):
    """Raised when there's insufficient inventory"""
    pass


class EmailException(BaseException):
    """Raised when email sending fails"""
    pass