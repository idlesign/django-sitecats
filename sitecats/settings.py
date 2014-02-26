from django.conf import settings


MODEL_CATEGORY = getattr(settings, 'SITECATS_MODEL_CATEGORY', 'sitecats.Category')
MODEL_FLAG = getattr(settings, 'SITECATS_MODEL_FLAG', 'sitecats.Flag')
