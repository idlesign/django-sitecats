from django.conf import settings


MODEL_CATEGORY = getattr(settings, 'SITECATS_MODEL_CATEGORY', 'sitecats.Category')
MODEL_TIE = getattr(settings, 'SITECATS_MODEL_TIE', 'sitecats.Tie')
