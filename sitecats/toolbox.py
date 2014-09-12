from inspect import getargspec
from collections import namedtuple, OrderedDict

from django.utils.translation import ugettext_lazy as _, ungettext_lazy as _n
from django.utils.six import string_types
from django.contrib import messages

from .utils import get_category_model, Cache
from .exceptions import SitecatsConfigurationError, SitecatsSecurityException, SitecatsNewCategoryException, SitecatsValidationError


SITECATS_CACHE = Cache()  # Caching object.


class CategoryList(object):
    """Represents a set on categories under a parent category on page."""
    _cache_category = None

    #TODO custom template

    def __init__(self, alias=None, show_title=False, show_links=True, cat_html_class=''):
        """
        :param str alias: Alias of a category to construct a list from (list will include subcategories)
        :param bool show_title: Flag to render parent category title
        :param bool show_links: Flag to render links for category pages
        :param str cat_html_class: HTML classes to be added to categories
        :return:
        """
        self.alias = alias
        self.show_title = show_title
        self.show_links = show_links
        self.cat_html_class = cat_html_class
        self.obj = None
        self.editor = None

    def set_obj(self, obj):
        """Sets a target object for categories to be filtered upon.

        `ModelWithCategory` heir is expected.

        If not set CategoryList will render actual categories.
        If set CategoryList will render just object-to-categories ties.

        :param obj: `ModelWithCategory` heir
        :return:
        """
        self.obj = obj

    def enable_editor(self, allow_add=True, allow_remove=False, allow_new=False, min_num=None, max_num=None, render_button=True):
        """Enables editor controls for this category list.

        :param bool allow_add: Flag to allow adding object-to-categories ties
        :param bool allow_remove: Flag to allow remove of object-to-categories ties or categories themselves
        :param bool allow_new: Flag to allow new categories creation
        :param None|int min_num: Child items minimum for this list (object-to-categories ties or categories themselves)
        :param None|int max_num: Child items maximum for this list (object-to-categories ties or categories themselves)
        :param bool render_button: Flag to allow buttons rendering for forms of this list
        :return:
        """
        # DRY: translate method args into namedtuple args.
        args, n, n, n = getargspec(self.enable_editor)
        locals_ = locals()
        self.editor = namedtuple('CategoryEditor', args)(**{arg: locals_[arg] for arg in args})

    def get_category_model(self):
        """Returns category model for this list (parent category for categories in the list).

        :return: CategoryModel
        """
        if self._cache_category is None:
            self._cache_category = SITECATS_CACHE.get_category_by_alias(self.alias)
        return self._cache_category

    def get_category_attr(self, name, default=False):
        """Returns a custom attribute of a category model for this list.

        :param str name: Attribute name
        :param default: Default value if attribute is not found
        :return: attribute value
        """
        category = self.get_category_model()
        return getattr(category, name, default)

    def get_id(self):
        """Returns ID attribute of a category of this list.

        :rtype: int|None
        :return: id
        """
        return self.get_category_attr('id', None)

    def get_title(self):
        """Returns `title` attribute of a category of this list.

        :rtype: str
        :return: title
        """
        return self.get_category_attr('title', _('Categories'))

    def get_note(self):
        """Returns `note` attribute of a category of this list.

        :rtype: str
        :return: note
        """
        return self.get_category_attr('note', '')

    def get_categories(self):
        """Returns a list of actual subcategories.

        :rtype: list
        :return: a list of actual subcategories
        """
        return SITECATS_CACHE.get_categories(self.alias, self.obj)


class CategoryRequestHandler(object):
    """This one can handle requests issued by CategoryList editors. Can be used in views."""

    list_cls = CategoryList  # For customization purposes.
    KNOWN_ACTIONS = ('add', 'remove')

    def __init__(self, request, obj=None):
        """
        :param Request request: Django request object
        :param Model obj: `ModelWithCategory` heir to bind CategoryList objects upon.
        :return:
        """
        self._request = request
        self._lists = OrderedDict()
        self._obj = obj

    def register_lists(self, category_lists, lists_init_kwargs=None, editor_init_kwargs=None):
        """Registers CategoryList objects to handle their requests.

        :param list category_lists: CategoryList objects
        :param dict lists_init_kwargs: Attributes to apply to each of CategoryList objects
        :return:
        """
        lists_init_kwargs = lists_init_kwargs or {}
        editor_init_kwargs = editor_init_kwargs or {}

        for lst in category_lists:
            if isinstance(lst, string_types):  # Spawn CategoryList object from base category alias.
                lst = self.list_cls(lst, **lists_init_kwargs)
            elif not isinstance(lst, CategoryList):
                raise SitecatsConfigurationError('`CategoryRequestHandler.register_lists()` accepts only `CategoryList` objects or category aliases.')

            if self._obj:
                lst.set_obj(self._obj)

            for name, val in lists_init_kwargs.items():  # Setting CategoryList attributes from kwargs.
                setattr(lst, name, val)

            lst.enable_editor(**editor_init_kwargs)

            self._lists[lst.get_id()] = lst

    @classmethod
    def action_remove(cls, request, category_list):
        """Handles `remove` action from CategoryList editor.

        Removes an actual category if a target object is not set for the list.
        Removes a tie-to-category object if a target object is set for the list.

        :param Request request: Django request object
        :param CategoryList category_list: CategoryList object to operate upon.
        :return: True on success otherwise and exception from SitecatsException family is raised.
        """
        if not category_list.editor.allow_remove:
            raise SitecatsSecurityException('`action_remove()` is not supported by parent `%s`category.' % category_list.alias)

        category_id = int(request.POST.get('category_id', 0))
        if not category_id:
            raise SitecatsSecurityException('Unsupported `category_id` value - `%s` - is passed to `action_remove()`.' % category_id)

        category = SITECATS_CACHE.get_category_by_id(category_id)
        if not category:
            raise SitecatsSecurityException('Unable to get `%s` category in `action_remove()`.' % category_id)

        cat_ident = category.alias or category.id

        if category.is_locked:
            raise SitecatsSecurityException('`action_remove()` is not supported by `%s` category.' % cat_ident)

        if category.parent_id != category_list.get_id():
            raise SitecatsSecurityException('`action_remove()` is unable to remove `%s`: not a child of parent `%s` category.' % (cat_ident, category_list.alias))

        min_num = category_list.editor.min_num

        def check_min_num(num):
            if min_num is not None and num-1 < min_num:
                raise SitecatsValidationError(_('Unable to remove "%s" category from "%s": parent category requires at least %s %s.') % (category.title, category_list.get_title(), min_num, _n('subcategory', 'subcategories', min_num)))

        child_ids = SITECATS_CACHE.get_child_ids(category_list.alias)
        check_min_num(len(child_ids))
        if category_list.obj is None:  # Remove category itself and children.
            category.delete()
        else:  # Remove just a category-to-object tie.
            # TODO filter user/status
            check_min_num(category_list.obj.get_ties_for_categories_qs(child_ids).count())
            category_list.obj.remove_from_category(category)

        return True

    @classmethod
    def action_add(cls, request, category_list):
        """Handles `add` action from CategoryList editor.

        Adds an actual category if a target object is not set for the list.
        Adds a tie-to-category object if a target object is set for the list.

        :param Request request: Django request object
        :param CategoryList category_list: CategoryList object to operate upon.
        :return: CategoryModel object on success otherwise and exception from SitecatsException family is raised.
        """
        if not category_list.editor.allow_add:
            raise SitecatsSecurityException('`action_add()` is not supported by `%s` category.' % category_list.alias)

        category_title = request.POST.get('category_title', '').strip()
        if not category_title:
            raise SitecatsSecurityException('Unsupported `category_title` value - `%s` - is passed to `action_add()`.' % category_title)

        exists = SITECATS_CACHE.find_category(category_list.alias, category_title)

        if exists and category_list.obj is None:  # Already exists.
            return exists

        if not exists and not category_list.editor.allow_new:
            raise SitecatsNewCategoryException(_('Unable to create a new "%s" category inside of "%s": parent category does not support this action.') % (category_title, category_list.get_title()))

        max_num = category_list.editor.max_num

        def check_max_num(num):
            if max_num is not None and num+1 > max_num:
                raise SitecatsValidationError(_('Unable to add "%s" category into "%s": parent category can have at most %s %s.') % (category_title, category_list.get_title(), max_num, _n('subcategory', 'subcategories', max_num)))

        child_ids = SITECATS_CACHE.get_child_ids(category_list.alias)
        if not exists:  # Add new category.
            if category_list.obj is None:
                check_max_num(len(child_ids))
            # TODO status
            target_category = get_category_model().add(category_title, request.user, parent=category_list.get_category_model())
        else:
            target_category = exists  # Use existing one for a tie.

        if category_list.obj is not None:
            # TODO status
            check_max_num(category_list.obj.get_ties_for_categories_qs(child_ids).count())
            category_list.obj.add_to_category(target_category, request.user)

        return target_category

    def listen(self):
        """Instructs handler to listen to Django request and handle
        CategoryList editor requests (if any).

        :return: None on success otherwise and exception from SitecatsException family is raised.
        """
        requested_action = self._request.POST.get('category_action', False)

        if not requested_action:
            return None  # No action supplied. Pass.

        if requested_action not in self.KNOWN_ACTIONS:
            raise SitecatsSecurityException('Unknown `category_action` - `%s` - requested.')

        category_base_id = self._request.POST.get('category_base_id', False)
        if category_base_id == 'None':
            category_base_id = None
        else:
            category_base_id = int(category_base_id)
        if category_base_id not in self._lists.keys():
            raise SitecatsSecurityException('Unknown `category_base_id` - `%s` - requested.')

        category_list = self._lists[category_base_id]
        if category_list.editor is None:
            raise SitecatsSecurityException('Editor is disabled for `%s` category.' % category_list.alias)

        action_method = getattr(self, 'action_%s' % requested_action)

        # TODO Customize messages.
        try:
            return action_method(self._request, category_list)
        except SitecatsNewCategoryException as e:
            messages.error(self._request, e)
            return None
        except SitecatsValidationError as e:
            messages.error(self._request, e.messages[0])
            return None
        finally:
            self._request.POST = {}  # Prevent other forms fail.

    def get_lists(self):
        """Returns a list of previously registered CategoryList objects.

        :rtype: list
        :return: A list of CategoryList objects.
        """
        return list(self._lists.values())
