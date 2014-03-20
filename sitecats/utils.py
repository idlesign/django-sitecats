from django.contrib.contenttypes.models import ContentType
from django.db.models import get_model
from django.core.exceptions import ImproperlyConfigured

from sitecats import settings


def get_app_n_model(settings_entry_name):
    """Returns tuple with application and model class names."""
    try:
        app_name, model_name = getattr(settings, settings_entry_name).split('.')
    except ValueError:
        raise ImproperlyConfigured('`SITECATS_%s` must have the following format: `app_name.model_name`.' % settings_entry_name)
    return app_name, model_name


def get_model_class(settings_entry_name):
    """Returns a certain model as defined in the project settings."""
    app_name, model_name = get_app_n_model(settings_entry_name)
    model = get_model(app_name, model_name)

    if model is None:
        raise ImproperlyConfigured('`SITECATS_%s` refers to model `%s` that has not been installed.' % (settings_entry_name, model_name))

    return model


def get_category_model():
    """Returns the Category model, set for the project."""
    return get_model_class('MODEL_CATEGORY')


def get_flag_model():
    """Returns the Flag model, set for the project."""
    return get_model_class('MODEL_FLAG')


def get_tags(category, target_object):
    """Returns a list of tags in the given category associated
    with the given object.

    """
    # TODO category filtering
    # TODO reduce db hits (category.title)
    flag_model = get_flag_model()

    items = []
    if target_object is not None:
        content_type = ContentType.objects.get_for_model(target_object)
        items = flag_model.objects.filter(content_type=content_type, object_id=target_object.id, category__isnull=False).all()

    return items
