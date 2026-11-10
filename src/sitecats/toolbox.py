from inspect import getfullargspec
from collections import namedtuple
from typing import List, Callable, Union, Optional, Any, Tuple, Dict

from django.db.models import Model
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _, ngettext_lazy
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from sitecats.models import ModelWithCategory

from .settings import UNRESOLVED_URL_MARKER
from .utils import get_category_model, get_tie_model, get_cache
from .exceptions import SitecatsConfigurationError, SitecatsSecurityException, SitecatsNewCategoryException, \
    SitecatsValidationError

if False:  # pragma: nocover
    from .models import CategoryBase # noqa


def get_category_aliases_under(parent_alias: str = None) -> List[str]:
    """Returns a list of category aliases under the given parent.

    Could be useful to pass to `ModelWithCategory.enable_category_lists_editor`
    in `additional_parents_aliases` parameter.

    :param parent_alias: Parent alias or None to categories under root

    """
    return [ch.alias for ch in get_cache().get_children_for(parent_alias, only_with_aliases=True)]


def get_category_lists(
        init_kwargs: dict = None,
        additional_parents_aliases: List[str] = None,
        obj: Model = None

) -> List['CategoryList']:
    """Returns a list of CategoryList objects, optionally associated with
    a given model instance.

    :param init_kwargs:
    :param additional_parents_aliases:
    :param obj: Model instance to get categories for

    """
    init_kwargs = init_kwargs or {}
    additional_parents_aliases = additional_parents_aliases or []

    parent_aliases = additional_parents_aliases

    if obj is not None:
        ctype = ContentType.objects.get_for_model(obj)
        cat_ids = [
            item[0] for item in
            get_tie_model().objects.filter(content_type=ctype, object_id=obj.id).values_list('category_id').all()
        ]
        parent_aliases = list(get_cache().get_parents_for(cat_ids).union(additional_parents_aliases))

    lists = []

    aliases = get_cache().sort_aliases(parent_aliases)
    categories_cache = get_cache().get_categories(aliases, obj)

    for parent_alias in aliases:
        catlist = CategoryList(parent_alias, **init_kwargs)  # TODO Burned in class name. Make more customizable.

        if obj is not None:
            catlist.set_obj(obj)

        # Optimization. To get DB hits down.
        cache = []

        try:
            cache = categories_cache[parent_alias]

        except KeyError:
            pass

        catlist.set_get_categories_cache(cache)

        lists.append(catlist)

    return lists


class CategoryList:
    """Represents a set on categories under a parent category on page."""

    _cache_category = None
    _cache_get_categories = None

    #TODO custom template

    def __init__(
            self,
            alias: str = None,
            show_title: bool = False,
            show_links: Union[bool, Callable] = True,
            cat_html_class: str = ''
    ):
        """
        :param alias: Alias of a category to construct a list from (list will include subcategories)

        :param show_title: Flag to render parent category title

        :param show_links: Boolean flag to render links for category pages,
            or a callable which accepts Category instance and returns an URL for it.
            If boolean and True links will be set to UNRESOLVED_URL_MARKER (useful
            for client-side links generation based on data-* attrs of HTML elements).

        :param cat_html_class: HTML classes to be added to categories

        """
        self.alias = alias
        self.show_title = show_title
        self._url_resolver = None

        if callable(show_links):
            self._url_resolver = show_links
            show_links = True

        self.show_links = show_links
        self.cat_html_class = cat_html_class
        self.obj: Optional['ModelWithCategory'] = None
        self.editor: namedtuple = None

    def __str__(self) ->  str:
        """Returns alias."""
        return self.alias or ''

    def set_get_categories_cache(self, val: list):
        """Sets prefetched data to be returned by `get_categories()` later on.

        :param val:

        """
        self._cache_get_categories = val

    def get_category_url(self, category: 'CategoryBase') -> str:
        """Returns URL for a given Category object from this list.

         First tries to get it with a callable passed as `show_links` init param of this list.
         Secondly tries to get it with `get_category_absolute_url` method of an object associated with this list.

        :param category:

        """
        if self._url_resolver is not None:
            return self._url_resolver(category)

        if self.obj:
            get_url = getattr(self.obj, 'get_category_absolute_url', None)
            if get_url:
                return get_url(category)

        return UNRESOLVED_URL_MARKER

    def set_obj(self, obj: 'ModelWithCategory'):
        """Sets a target object for categories to be filtered upon.

        `ModelWithCategory` heir is expected.

        If not set CategoryList will render actual categories.
        If set CategoryList will render just object-to-categories ties.

        :param obj: `ModelWithCategory` heir

        """
        self.obj = obj

    def enable_editor(
            self,
            allow_add: bool = True,
            allow_remove: bool = False,
            allow_new: bool = False,
            min_num: int = None,
            max_num: int = None,
            render_button: bool = True,
            category_separator: str = None,
            show_category_choices: bool = True
    ):
        """Enables editor controls for this category list.

        :param allow_add: Flag to allow adding object-to-categories ties

        :param allow_remove: Flag to allow remove of object-to-categories ties or categories themselves

        :param allow_new: Flag to allow new categories creation

        :param min_num: Child items minimum for this list
            (object-to-categories ties or categories themselves)

        :param max_num: Child items maximum for this list
            (object-to-categories ties or categories themselves)

        :param render_button: Flag to allow buttons rendering for forms of this list

        :param category_separator: String to consider it a category separator.

        :param show_category_choices: Flag to render a choice list of available subcategories
            for each CategoryList

        """
        # DRY: translate method args into namedtuple args.
        args = getfullargspec(self.enable_editor)[0]
        locals_ = locals()
        self.editor = namedtuple('CategoryEditor', args)(**{arg: locals_[arg] for arg in args})

    def get_category_model(self) -> Optional['CategoryBase']:
        """Returns category model for this list (parent category for categories in the list) or None."""

        if self._cache_category is None:
            self._cache_category = get_cache().get_category_by_alias(self.alias)

        return self._cache_category

    def get_category_attr(self, name: str, default: Any = False) -> Any:
        """Returns a custom attribute of a category model for this list.

        :param name: Attribute name
        :param default: Default value if attribute is not found

        """
        category = self.get_category_model()
        return getattr(category, name, default)

    def get_id(self) -> Optional[int]:
        """Returns ID attribute of a category of this list."""
        return self.get_category_attr('id', None)

    def get_title(self) -> str:
        """Returns `title` attribute of a category of this list."""
        return self.get_category_attr('title', _('Categories'))

    def get_note(self) -> str:
        """Returns `note` attribute of a category of this list."""
        return self.get_category_attr('note', '')

    def get_categories(self, tied_only: bool = None) -> List['CategoryBase']:
        """Returns a list of actual subcategories.

        :param tied_only: Flag to get only categories with ties. Ties stats are stored in `ties_num` attrs.

        """
        if self._cache_get_categories is not None:
            return self._cache_get_categories

        if tied_only is None:
            tied_only = self.obj is not None

        return get_cache().get_categories(self.alias, self.obj, tied_only=tied_only)

    def get_choices(self) -> List['CategoryBase']:
        """Returns available subcategories choices list."""
        return get_cache().get_children_for(self.alias)


class CategoryRequestHandler:
    """This one can handle requests issued by CategoryList editors. Can be used in views."""

    list_cls: CategoryList = CategoryList  # For customization purposes.
    KNOWN_ACTIONS: Tuple[str, ...] = ('add', 'remove')

    def __init__(self, request: HttpRequest, obj: 'ModelWithCategory' = None, error_messages_extra_tags: str = None):
        """
        :param Request request: Django request object
        :param Model obj: `ModelWithCategory` heir to bind CategoryList objects upon.
        :param error_messages_extra_tags:

        """
        self._request = request
        self._lists = {}
        self._obj = obj
        self.error_messages_extra_tags = error_messages_extra_tags or ''

    def register_lists(
            self,
            category_lists: List[CategoryList],
            lists_init_kwargs: Dict[str, Any] = None,
            editor_init_kwargs: Dict[str, Any] = None
    ):
        """Registers CategoryList objects to handle their requests.

        :param category_lists: CategoryList objects
        :param lists_init_kwargs: Attributes to apply to each of CategoryList objects
        :param editor_init_kwargs:

        """
        lists_init_kwargs = lists_init_kwargs or {}
        editor_init_kwargs = editor_init_kwargs or {}

        for lst in category_lists:

            if isinstance(lst, str):  # Spawn CategoryList object from base category alias.
                lst = self.list_cls(lst, **lists_init_kwargs)

            elif not isinstance(lst, CategoryList):
                raise SitecatsConfigurationError(
                    '`CategoryRequestHandler.register_lists()` accepts only '
                    '`CategoryList` objects or category aliases.'
                )

            if self._obj:
                lst.set_obj(self._obj)

            for name, val in lists_init_kwargs.items():  # Setting CategoryList attributes from kwargs.
                setattr(lst, name, val)

            lst.enable_editor(**editor_init_kwargs)

            self._lists[lst.get_id()] = lst

    @classmethod
    def action_remove(cls, request: HttpRequest, category_list: CategoryList) -> bool:
        """Handles `remove` action from CategoryList editor.

        Returns True on success otherwise and exception from SitecatsException family is raised.

        Removes an actual category if a target object is not set for the list.
        Removes a tie-to-category object if a target object is set for the list.

        :param request: Django request object
        :param category_list: CategoryList object to operate upon.

        """
        if not category_list.editor.allow_remove:
            raise SitecatsSecurityException(
                f'`action_remove()` is not supported by parent `{category_list.alias}`category.')

        category_id = int(request.POST.get('category_id', 0))

        if not category_id:
            raise SitecatsSecurityException(
                f'Unsupported `category_id` value - `{category_id}` - is passed to `action_remove()`.')

        category = get_cache().get_category_by_id(category_id)
        if not category:
            raise SitecatsSecurityException(f'Unable to get `{category_id}` category in `action_remove()`.')

        cat_ident = category.alias or category.id

        if category.is_locked:
            raise SitecatsSecurityException(f'`action_remove()` is not supported by `{cat_ident}` category.')

        if category.parent_id != category_list.get_id():
            raise SitecatsSecurityException(
                f'`action_remove()` is unable to remove `{cat_ident}`: '
                f'not a child of parent `{category_list.alias}` category.'
            )

        min_num = category_list.editor.min_num

        def check_min_num(num: int):
            if min_num is not None and num-1 < min_num:
                subcats_str = ngettext_lazy('subcategory', 'subcategories', min_num)
                error_msg = _(
                    'Unable to remove "%(target_category)s" category from "%(parent_category)s": '
                    'parent category requires at least %(num)s %(subcats_str)s.'
                ) % {
                    'target_category': category.title,
                    'parent_category': category_list.get_title(),
                    'num': min_num,
                    'subcats_str': subcats_str
                }
                raise SitecatsValidationError(error_msg)

        child_ids = get_cache().get_child_ids(category_list.alias)

        check_min_num(len(child_ids))

        if category_list.obj is None:  # Remove category itself and children.
            category.delete()

        else:  # Remove just a category-to-object tie.
            # TODO filter user/status
            check_min_num(category_list.obj.get_ties_for_categories_qs(child_ids).count())
            category_list.obj.remove_from_category(category)

        return True

    @classmethod
    def action_add(cls, request: HttpRequest, category_list: CategoryList) -> 'CategoryBase':
        """Handles `add` action from CategoryList editor.
        Returns CategoryModel object on success otherwise and exception from SitecatsException family is raised.

        Adds an actual category if a target object is not set for the list.
        Adds a tie-to-category object if a target object is set for the list.

        :param request: Django request object
        :param category_list: CategoryList object to operate upon.

        """
        if not category_list.editor.allow_add:
            raise SitecatsSecurityException(f'`action_add()` is not supported by `{category_list.alias}` category.')

        titles = request.POST.get('category_title', '').strip()
        if not titles:
            raise SitecatsSecurityException(
                f'Unsupported `category_title` value - `{titles}` - is passed to `action_add()`.')

        if category_list.editor.category_separator is None:
            titles = [titles]

        else:
            titles = [
                title.strip()
                for title in titles.split(category_list.editor.category_separator)
                if title.strip()
            ]

        def check_max_num(num: int, max_num: Optional[int], category_title: str):
            if max_num is not None and num+1 > max_num:
                subcats_str = ngettext_lazy('subcategory', 'subcategories', max_num)
                error_msg = _(
                    'Unable to add "%(target_category)s" category into "%(parent_category)s": '
                    'parent category can have at most %(num)s %(subcats_str)s.'
                ) % {
                    'target_category': category_title,
                    'parent_category': category_list.get_title(),
                    'num': max_num,
                    'subcats_str': subcats_str
                }
                raise SitecatsValidationError(error_msg)

        target_category = None

        for category_title in titles:
            exists = get_cache().find_category(category_list.alias, category_title)

            if exists and category_list.obj is None:  # Already exists.
                return exists

            if not exists and not category_list.editor.allow_new:
                error_msg = _(
                    'Unable to create a new "%(new_category)s" category inside of "%(parent_category)s": '
                    'parent category does not support this action.'
                ) % {
                    'new_category': category_title,
                    'parent_category': category_list.get_title()
                }
                raise SitecatsNewCategoryException(error_msg)

            max_num = category_list.editor.max_num
            child_ids = get_cache().get_child_ids(category_list.alias)

            if not exists:  # Add new category.

                if category_list.obj is None:
                    check_max_num(len(child_ids), max_num, category_title)

                # TODO status
                target_category = get_category_model().add(
                    category_title, request.user, parent=category_list.get_category_model()
                )

            else:
                target_category = exists  # Use existing one for a tie.

            if category_list.obj is not None:
                # TODO status
                check_max_num(
                    category_list.obj.get_ties_for_categories_qs(child_ids).count(),
                    max_num,
                    category_title
                )
                category_list.obj.add_to_category(target_category, request.user)

        return target_category

    def listen(self) -> Any:
        """Instructs handler to listen to Django request and handle
        CategoryList editor requests (if any).

        Returns None on success otherwise and exception from SitecatsException family is raised.

        """
        requested_action = self._request.POST.get('category_action', False)

        if not requested_action:
            return None  # No action supplied. Pass.

        if requested_action not in self.KNOWN_ACTIONS:
            raise SitecatsSecurityException(f'Unknown `category_action` requested: `{requested_action}`.')

        category_base_id = self._request.POST.get('category_base_id', False)

        if category_base_id == 'None':
            category_base_id = None

        else:
            category_base_id = int(category_base_id)

        if category_base_id not in self._lists.keys():
            raise SitecatsSecurityException(f'Unknown `category_base_id` requested: `{category_base_id}`.')

        category_list = self._lists[category_base_id]
        if category_list.editor is None:
            raise SitecatsSecurityException(f'Editor is disabled for `{category_list.alias}` category.')

        action_method = getattr(self, f'action_{requested_action}')

        try:
            return action_method(self._request, category_list)

        except SitecatsNewCategoryException as e:
            messages.error(self._request, e, extra_tags=self.error_messages_extra_tags, fail_silently=True)
            return None

        except SitecatsValidationError as e:
            messages.error(self._request, e.messages[0], extra_tags=self.error_messages_extra_tags, fail_silently=True)
            return None

        finally:
            self._request.POST = {}  # Prevent other forms fail.

    def get_lists(self) -> List[CategoryList]:
        """Returns a list of previously registered CategoryList objects."""
        return list(self._lists.values())
