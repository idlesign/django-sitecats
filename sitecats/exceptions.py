from django.core.exceptions import ImproperlyConfigured, SuspiciousOperation
from django.forms.fields import ValidationError


class SitecatsException(Exception):
    """Base sitecats exception."""


class SitecatsConfigurationError(SitecatsException, ImproperlyConfigured):
    """Exception for sitecats configuration errors."""


class SitecatsSecurityException(SitecatsException, SuspiciousOperation):
    """Exception raised by CategoryRequestHandler on suspicious request data."""


class SitecatsNewCategoryException(SitecatsSecurityException):
    """Exception raised by CategoryRequestHandler when a try to add a subcategory into a restricted
    category is detected.

    """


class SitecatsLockedCategoryDelete(SitecatsException):
    """Exception raised when a try to delete() a locked category is detected."""


class SitecatsValidationError(SitecatsException, ValidationError):
    """Exception raised by CategoryRequestHandler on request data validation errors."""

