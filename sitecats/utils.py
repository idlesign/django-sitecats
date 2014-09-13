from collections import OrderedDict

from etc.toolbox import get_model_class_from_settings
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.db.models import signals, Count, Model

from sitecats import settings


def get_category_model():
    """Returns the Category model, set for the project."""
    return get_model_class_from_settings(settings, 'MODEL_CATEGORY')


def get_tie_model():
    """Returns the Tie model, set for the project."""
    return get_model_class_from_settings(settings, 'MODEL_TIE')


class Cache(object):

    # Sitecats objects are stored in Django cache for a year (60 * 60 * 24 * 365 = 31536000 sec).
    # Cache is only invalidated on sitecats Category model save/delete.
    CACHE_TIMEOUT = 31536000
    CACHE_ENTRY_NAME = 'sitecats'

    CACHE_NAME_IDS = 'ids'
    CACHE_NAME_ALIASES = 'aliases'
    CACHE_NAME_PARENTS = 'parents'

    def __init__(self):
        self._cache = None
        # Listen for signals from the models.
        category_model = get_category_model()
        signals.post_save.connect(self._cache_empty, sender=category_model)
        signals.post_delete.connect(self._cache_empty, sender=category_model)

    def _cache_init(self):
        """Initializes local cache from Django cache if required."""
        cache_ = cache.get(self.CACHE_ENTRY_NAME)

        if cache_ is None:
            categories = get_category_model().objects.order_by('sort_order')

            ids = {category.id: category for category in categories}
            aliases = {category.alias: category for category in categories if category.alias}

            parent_to_children = OrderedDict()  # Preserve aliases order.
            for category in categories:
                parent_category = ids.get(category.parent_id, False)
                parent_alias = None
                if parent_category:
                    parent_alias = parent_category.alias
                if parent_alias not in parent_to_children:
                    parent_to_children[parent_alias] = []
                parent_to_children[parent_alias].append(category.id)

            cache_ = {
                self.CACHE_NAME_IDS: ids,
                self.CACHE_NAME_PARENTS: parent_to_children,
                self.CACHE_NAME_ALIASES: aliases
            }

            cache.set(self.CACHE_ENTRY_NAME, cache_, self.CACHE_TIMEOUT)

        self._cache = cache_

    def _cache_empty(self, **kwargs):
        """Empties cached sitecats data."""
        self._cache = None
        cache.delete(self.CACHE_ENTRY_NAME)

    def _cache_get_entry(self, entry_name, key=0, default=False):
        """Returns cache entry parameter value by its name."""
        if key == 0:
            return self._cache[entry_name]
        return self._cache[entry_name].get(key, default)

    def sort_aliases(self, aliases):
        """Sorts the given aliases list, returns a sorted list.

        :param list aliases:
        :return: sorted aliases list
        """
        self._cache_init()
        if not aliases:
            return aliases
        parent_aliases = self._cache_get_entry(self.CACHE_NAME_PARENTS).keys()
        return [parent_alias for parent_alias in parent_aliases if parent_alias in aliases]

    def get_parents_for(self, child_ids):
        """Returns parent aliases for a list of child IDs.

        :param list child_ids:
        :rtype: set
        :return: a set of parent aliases
        """
        self._cache_init()
        parent_candidates = []
        for parent, children in self._cache_get_entry(self.CACHE_NAME_PARENTS).items():
            if set(children).intersection(child_ids):
                parent_candidates.append(parent)
        return set(parent_candidates)  # Make unique.

    def get_children_for(self, parent_alias=None, only_with_aliases=False):
        """Returns a list with with categories under the given parent.

        :param str|None parent_alias: Parent category alias or None for categories under root
        :param bool only_with_aliases: Flag to return only children with aliases
        :return: a list of category objects
        """
        self._cache_init()
        child_ids = self.get_child_ids(parent_alias)
        if only_with_aliases:
            children = []
            for cid in child_ids:
                category = self.get_category_by_id(cid)
                if category.alias:
                    children.append(category)
            return children
        return [self.get_category_by_id(cid) for cid in child_ids]

    def get_child_ids(self, parent_alias):
        """Returns child IDs of the given parent category

        :param str parent_alias: Parent category alias
        :rtype: list
        :return: a list of child IDs
        """
        self._cache_init()
        return self._cache_get_entry(self.CACHE_NAME_PARENTS, parent_alias, [])

    def get_category_by_alias(self, alias):
        """Returns Category object by its alias.

        :param str alias:
        :rtype: Category|None
        :return: category object
        """
        self._cache_init()
        return self._cache_get_entry(self.CACHE_NAME_ALIASES, alias, None)

    def get_category_by_id(self, id):
        """Returns Category object by its id.

        :param str alias:
        :rtype: Category
        :return: category object
        """
        self._cache_init()
        return self._cache_get_entry(self.CACHE_NAME_IDS, id)

    def find_category(self, parent_alias, title):
        """Searches parent category children for the given title (case independent).

        :param str parent_alias:
        :param str title:
        :rtype: Category|None
        :return: None if not found; otherwise - found Category
        """
        found = None
        child_ids = self.get_child_ids(parent_alias)
        for cid in child_ids:
            category = self.get_category_by_id(cid)
            if category.title.lower() == title.lower():
                found = category
                break
        return found

    def get_categories(self, parent_alias=None, target_object=None):
        """Returns subcategories (or ties if `target_object` is set)
        for the given parent category.

        :param str parent_alias:
        :param ModelWithCategory|Model target_object:
        :return: a list of category objects or tie objects extended with information from their categories.
        """
        if target_object is None:  # No filtering by object, list all known categories.
            return self.get_children_for(parent_alias)
        else:
            filter_kwargs = {}
            child_ids = self.get_child_ids(parent_alias)
            if not child_ids:
                return []
            filter_kwargs.update({
                'content_type': ContentType.objects.get_for_model(target_object),
                'object_id': target_object.id,
                'category_id__in': child_ids
            })

            # Calculating categories weight too.
            # dicts with `ties_num` and `category_id`
            stats = {item['category_id']: item['ties_num'] for item in  get_tie_model().objects.filter(**filter_kwargs).values('category_id').annotate(ties_num=Count('category'))}
            categories = []
            for cat_id, ties_num in stats.items():
                cat = self.get_category_by_id(cat_id)
                cat.ties_num = ties_num
                categories.append(cat)
            return categories
