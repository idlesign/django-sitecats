"""MkDocs hooks.

Configure Django to make `sitecats` modules importable
for the apidescribed plugin during documentation builds.

"""
import django
from django.conf import settings


def on_startup(**kwargs):

    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[
                'django.contrib.auth',
                'django.contrib.contenttypes',
                'sitecats',
            ],
        )
        django.setup()
