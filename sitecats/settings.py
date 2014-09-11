from django.conf import settings

# Path to a model to be used as a Category.
MODEL_CATEGORY = getattr(settings, 'SITECATS_MODEL_CATEGORY', 'sitecats.Category')

# Path to a model to be used as a category-to-object Tie.
MODEL_TIE = getattr(settings, 'SITECATS_MODEL_TIE', 'sitecats.Tie')
