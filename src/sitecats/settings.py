from django.conf import settings


MODEL_CATEGORY = getattr(settings, 'SITECATS_MODEL_CATEGORY', 'sitecats.Category')
"""A dotted path to a model to be used as a Category. E.g.: myapp.MyCategory"""

MODEL_TIE = getattr(settings, 'SITECATS_MODEL_TIE', 'sitecats.Tie')
"""A dotted path to a model to be used as a category-to-object Tie. E.g.: myapp.MyTie"""

UNRESOLVED_URL_MARKER = getattr(settings, 'SITECATS_UNRESOLVED_URL_MARKER', '#unresolved')
"""String returned instead of a category URL if unresolved."""
