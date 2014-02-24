from django.conf import settings


MODEL_CATEGORY = getattr(settings, 'SITECATS_MODEL_CATEGORY', 'sitecats.Category')
MODEL_TAG = getattr(settings, 'SITECATS_MODEL_TAG', 'sitecats.Tag')
