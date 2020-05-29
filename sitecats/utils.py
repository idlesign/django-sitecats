from typing import Type, Any, List, Set, Optional, Union, Dict

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.db.models import signals, Count, Model
from etc.toolbox import get_model_class_from_string

from .settings import MODEL_CATEGORY, MODEL_TIE

if False:  # pragma: nocover
    from .models import CategoryBase, TieBase, ModelWithCategory  # noqa


def get_category_model() -> Type['CategoryBase']:
    """Returns the Category model, set for the project."""
    return get_model_class_from_string(MODEL_CATEGORY)


def get_tie_model() -> Type['TieBase']:
    """Returns the Tie model, set for the project."""
    return get_model_class_from_string(MODEL_TIE)


_SITECATS_CACHE = None


def get_cache() -> 'Cache':
    """Returns global cache object."""

    global _SITECATS_CACHE

    if _SITECATS_CACHE is None:
        _SITECATS_CACHE = apps.get_app_config('sitecats').get_categories_cache()

    return _SITECATS_CACHE


class Cache:

    # Sitecats objects are stored in Django cache for a year (60 * 60 * 24 * 365 = 31536000 sec).
    # Cache is only invalidated on sitecats Category model save/delete.
    CACHE_TIMEOUT: str = 31536000
    CACHE_ENTRY_NAME: str = 'sitecats'

    CACHE_NAME_IDS: str = 'ids'
    CACHE_NAME_ALIASES: str = 'aliases'
    CACHE_NAME_PARENTS: str = 'parents'

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

            parent_to_children = {}

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

    ENTIRE_ENTRY_KEY = tuple()

    def _cache_get_entry(
            self,
            entry_name: str,
            key: Union[str, int] = ENTIRE_ENTRY_KEY,
            default: Any = False

    ) -> Any:
        """Returns cache entry parameter value by its name.

        :param entry_name:
        :param key:
        :param default:

        """
        if key is self.ENTIRE_ENTRY_KEY:
            return self._cache[entry_name]
        return self._cache[entry_name].get(key, default)

    def sort_aliases(self, aliases: List[str]) -> List[str]:
        """Sorts the given aliases list, returns a sorted list.

        :param aliases:

        """
        self._cache_init()
        if not aliases:
            return aliases
        parent_aliases = self._cache_get_entry(self.CACHE_NAME_PARENTS).keys()
        return [parent_alias for parent_alias in parent_aliases if parent_alias in aliases]

    def get_parents_for(self, child_ids: List[int]) -> Set[str]:
        """Returns parent aliases for a list of child IDs.

        :param child_ids:

        """
        self._cache_init()
        parent_candidates = []
        for parent, children in self._cache_get_entry(self.CACHE_NAME_PARENTS).items():
            if set(children).intersection(child_ids):
                parent_candidates.append(parent)
        return set(parent_candidates)  # Make unique.

    def get_children_for(self, parent_alias: str = None, only_with_aliases: bool = False) -> List['CategoryBase']:
        """Returns a list with with categories under the given parent.

        :param parent_alias: Parent category alias or None for categories under root
        :param only_with_aliases: Flag to return only children with aliases

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

    def get_child_ids(self, parent_alias: str) -> List[int]:
        """Returns child IDs of the given parent category

        :param parent_alias: Parent category alias

        """
        self._cache_init()
        return self._cache_get_entry(self.CACHE_NAME_PARENTS, parent_alias, [])

    def get_category_by_alias(self, alias: str) -> Optional['CategoryBase']:
        """Returns Category object by its alias.

        :param alias:

        """
        self._cache_init()
        return self._cache_get_entry(self.CACHE_NAME_ALIASES, alias, None)

    def get_category_by_id(self, cid: int) -> Optional['CategoryBase']:
        """Returns Category object by its id.

        :param cid:

        """
        self._cache_init()
        return self._cache_get_entry(self.CACHE_NAME_IDS, cid, None)

    def find_category(self, parent_alias: str, title: str) -> Optional['CategoryBase']:
        """Searches parent category children for the given title (case independent).

        :param parent_alias:
        :param title:

        """
        get_by_id = self.get_category_by_id

        for cid in self.get_child_ids(parent_alias):
            category = get_by_id(cid)
            if category and category.title.lower() == title.lower():
                return category

        return None

    def get_ties_stats(self, categories: List[int], target_model: Optional[Model] = None) -> Dict[int, int]:
        """Returns a dict with categories popularity stats.

        :param categories:
        :param target_model:

        """
        filter_kwargs = {
            'category_id__in': categories
        }

        if target_model is not None:
            is_cls = hasattr(target_model, '__name__')

            if is_cls:
                concrete = False

            else:
                concrete = True
                filter_kwargs['object_id'] = target_model.id

            filter_kwargs['content_type'] = ContentType.objects.get_for_model(
                target_model, for_concrete_model=concrete
            )

        return {
            item['category_id']: item['ties_num'] for item in
            get_tie_model().objects.filter(
                **filter_kwargs).values('category_id').annotate(ties_num=Count('category'))
        }

    def get_categories(
            self,
            parent_aliases: Optional[Union[str, List[str]]] = None,
            target_object: 'ModelWithCategory' = None,
            tied_only: bool = True
    ):
        """Returns subcategories (or ties if `target_object` is set)
        for the given parent category.

        :param parent_aliases:
        :param target_object:
        :param tied_only: Flag to get only categories with ties. Ties stats are stored in `ties_num` attrs.

        """
        single_mode = False
        if not isinstance(parent_aliases, list):
            single_mode = parent_aliases
            parent_aliases = [parent_aliases]

        all_children = []

        parents_to_children = {}

        for parent_alias in parent_aliases:
            child_ids = self.get_child_ids(parent_alias)
            parents_to_children[parent_alias] = child_ids
            if tied_only:
                all_children.extend(child_ids)

        ties = {}
        if tied_only:
            source = {}
            ties = self.get_ties_stats(all_children, target_object)
            for parent_alias, child_ids in parents_to_children.items():
                common = set(ties.keys()).intersection(child_ids)
                if common:
                    source[parent_alias] = common

        else:
            source = parents_to_children

        categories = {}

        for parent_alias, child_ids in source.items():

            for cat_id in child_ids:
                cat = self.get_category_by_id(cat_id)

                if tied_only:
                    cat.ties_num = ties.get(cat_id, 0)

                if parent_alias not in categories:
                    categories[parent_alias] = []

                categories[parent_alias].append(cat)

        if single_mode != False:  # sic!
            return categories[single_mode]

        return categories
