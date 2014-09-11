from django.core.exceptions import ImproperlyConfigured, SuspiciousOperation
from django.forms.fields import ValidationError


class SitecatsException(Exception):
    """"""


class SitecatsConfigurationError(SitecatsException, ImproperlyConfigured):
    """"""


class SitecatsSecurityException(SitecatsException, SuspiciousOperation):
    """"""


class SitecatsNewCategoryException(SitecatsSecurityException):
    """"""


class SitecatsLockedCategoryDelete(SitecatsException):
    """"""


class SitecatsValidationError(SitecatsException, ValidationError):
    """"""

