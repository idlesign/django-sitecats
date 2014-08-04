from collections import defaultdict

from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.db.models import signals, Count, Model

from .utils import get_category_model, get_flag_model


MODEL_CATEGORY_CLASS = get_category_model()
MODEL_FLAG_CLASS = get_flag_model()


# Sitecats objects are stored in Django cache for a year (60 * 60 * 24 * 365 = 31536000 sec).
# Cache is only invalidated on sitecats models change.
CACHE_TIMEOUT = 31536000
CACHE_ENTRY_NAME = 'sitecats'


class SiteCats(object):

    def __init__(self):
        self.cache = None
        # Listen for signals from the models.
        signals.post_save.connect(self.cache_empty, sender=MODEL_CATEGORY_CLASS)
        signals.post_delete.connect(self.cache_empty, sender=MODEL_CATEGORY_CLASS)

    def cache_init(self):
        """Initializes local cache from Django cache if required."""
        cache_ = cache.get(CACHE_ENTRY_NAME)

        if cache_ is None:
            categories = MODEL_CATEGORY_CLASS.objects.order_by('sort_order')

            ids = {category.id: category for category in categories}

            child_ids = defaultdict(list)
            for category in categories:
                parent_category = ids.get(category.parent_id, False)
                if parent_category:
                    child_ids[parent_category.alias].append(category.id)

            cache_ = {'ids': ids, 'child_ids': child_ids}

            cache.set(CACHE_ENTRY_NAME, cache_, CACHE_TIMEOUT)

        self.cache = cache_

    def cache_empty(self, **kwargs):
        """Empties cached sitecats data."""
        self.cache = None
        cache.delete(CACHE_ENTRY_NAME)

    def cache_get_entry(self, entry_name, key):
        """Returns cache entry parameter value by its name."""
        return self.cache[entry_name].get(key, False)

    def _populate_tags_data(self, tags, target_object):
        for tag in tags:
            # Attach category data from cache to prevent db hits.
            category = self.cache_get_entry('ids', tag['category_id'])
            tag.update(category.__dict__)
            tag['absolute_url'] = category.get_absolute_url(target_object)
        return tags

    def get_categories(self, category, target_object):
        """Returns a list of tags in a given category associated with a given object."""
        self.cache_init()

        filter_kwargs = {}

        category_kwargs = {'category__isnull': False}  # Tags are always linked to a category.
        if category is not None:
            children = self.cache_get_entry('child_ids', category)
            if children:
                category_kwargs = {'category_id__in': children}

        if target_object is not None:

            if not isinstance(target_object, Model):
                raise SiteCatsError('Object passed with `target_object` of `get_tags()` must be a model.')

            object_kwargs = {
                'content_type': ContentType.objects.get_for_model(target_object),
                'object_id': target_object.id
            }
            filter_kwargs.update(object_kwargs)

        filter_kwargs.update(category_kwargs)
        items = list(get_flag_model().objects.filter(**filter_kwargs).values('category_id').annotate(flags_num=Count('category')))
        return self._populate_tags_data(items, target_object)


class SiteCatsError(Exception):
    """Exception class for sitecats application."""
