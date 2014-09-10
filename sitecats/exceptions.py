
class SitecatsException(Exception):
    """"""


class SitecatsConfigurationError(SitecatsException):
    """"""


class SitecatsSecurityException(SitecatsException):
    """"""


class SitecatsNewCategoryException(SitecatsSecurityException):
    """"""


class SitecatsLockedCategoryDelete(SitecatsException):
    """"""

