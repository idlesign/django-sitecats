from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import python_2_unicode_compatible
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from .settings import MODEL_CATEGORY, MODEL_TIE
from .exceptions import SitecatsLockedCategoryDelete
from .utils import get_tie_model


USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


# This allows South to handle our custom 'CharFieldNullable' field.
if 'south' in settings.INSTALLED_APPS:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ['^sitecats\.models\.CharFieldNullable'])


class CharFieldNullable(models.CharField):
    """We use custom char field to put nulls in CategoryBase fields.
    That allows 'unique' param to be handled properly.

    """
    def get_prep_value(self, value):
        if value is not None:
            if value.strip() == '':
                return None
        return self.to_python(value)


@python_2_unicode_compatible
class CategoryBase(models.Model):
    """Base class for category models.

    Categories form a hierarchical registry to help structuring site entities.

    Inherit from this model and override SITECATS_MODEL_CATEGORY in settings.py
    to customize model fields and behaviour.

    """
    title = models.CharField(
        _('Title'), max_length=250, help_text=_('Category name.'))
    alias = CharFieldNullable(
        _('Alias'), max_length=80,
        help_text=_('Short name to address category from application code.'), blank=True, null=True, unique=True)
    is_locked = models.BooleanField(
        _('Locked'),
        help_text=_('Categories addressed from application code are locked, their aliases can not be changed. '
                    'Such categories can be deleted from application code only.'), default=False)

    parent = models.ForeignKey(
        'self', related_name='%(class)s_parents', verbose_name=_('Parent'),
        help_text=_('Parent category.'), db_index=True, null=True, blank=True)
    note = models.TextField(_('Note'), blank=True)

    status = models.IntegerField(_('Status'), null=True, blank=True, db_index=True)
    slug = CharFieldNullable(verbose_name=_('Slug'), unique=True, max_length=250, null=True, blank=True)

    creator = models.ForeignKey(USER_MODEL, related_name='%(class)s_creators', verbose_name=_('Creator'))
    time_created = models.DateTimeField(_('Date created'), auto_now_add=True)
    time_modified = models.DateTimeField(_('Date modified'), editable=False, auto_now=True)

    sort_order = models.PositiveIntegerField(
        _('Sort order'),
        help_text=_('Item position among other categories under the same parent.'), db_index=True, default=0)

    class Meta(object):
        abstract = True
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')
        unique_together = ('title', 'parent')

    @classmethod
    def add(cls, title, creator, parent=None):
        """Creates a category.

        :param str title:
        :param User creator:
        :param Category|None parent:
        :return:
        """
        obj = cls(title=title, creator=creator, parent=parent)
        obj.save()
        return obj

    def delete(self, *args, **kwargs):
        """Overridden to handle `is_locked`.

        :param args:
        :param kwargs:
        :return:
        """
        if self.is_locked:
            raise SitecatsLockedCategoryDelete('Unable to delete locked `%s` category.' % self)
        super(CategoryBase, self).delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        """Overridden to set sort order and sanitize title.

        :param args:
        :param kwargs:
        :return:
        """
        self.title = self.title.strip()
        super(CategoryBase, self).save(*args, **kwargs)
        if self.sort_order == 0:
            self.sort_order = self.id
            self.save()

    def __str__(self):
        alias = ''
        if self.alias:
            alias = ' (%s)' % self.alias
        return '%s%s' % (self.title, alias)


@python_2_unicode_compatible
class TieBase(models.Model):
    """Base class for ties models.

    Ties are relations between site entities and categories (see above).

    Inherit from this model and override SITECATS_MODEL_TIE in settings.py
    to customize model fields and behaviour.

    """
    category = models.ForeignKey(MODEL_CATEGORY, related_name='%(class)s_categories', verbose_name=_('Category'))
    note = models.TextField(_('Note'), blank=True)
    status = models.IntegerField(_('Status'), null=True, blank=True, db_index=True)

    creator = models.ForeignKey(USER_MODEL, related_name='%(class)s_creators', verbose_name=_('Creator'))
    time_created = models.DateTimeField(_('Date created'), auto_now_add=True)

    # Here follows a link to an object.
    object_id = models.PositiveIntegerField(verbose_name=_('Object ID'), db_index=True)
    content_type = models.ForeignKey(
        ContentType, verbose_name=_('Content type'), related_name='%(app_label)s_%(class)s_tags')

    linked_object = generic.GenericForeignKey()

    class Meta(object):
        abstract = True
        verbose_name = _('Tie')
        verbose_name_plural = _('Ties')

    def __str__(self):
        return '%s:%s tied to %s' % (self.content_type, self.object_id, self.category)


class Category(CategoryBase):
    """Built-in category class. Default functionality."""


class Tie(TieBase):
    """Built-in Tie class. Default functionality."""


class ModelWithCategory(models.Model):
    """Helper class for models with tags.

    Mix in this helper to your model class to be able to categorize model instances.

    """
    categories = generic.GenericRelation(MODEL_TIE)

    class Meta(object):
        abstract = True

    _category_lists_init_kwargs = None
    _category_editor = None

    def set_category_lists_init_kwargs(self, kwa_dict):
        """Sets keyword arguments for category lists which can be spawned
        by get_categories().

        :param dict|None kwa_dict:
        :return:
        """
        self._category_lists_init_kwargs = kwa_dict

    def get_category_lists(self, init_kwargs=None, additional_parents_aliases=None):
        """Returns a list of CategoryList objects, associated with
        this model instance.

        :param dict|None init_kwargs:
        :param list|None additional_parents_aliases:
        :rtype: list|CategoryRequestHandler
        :return:
        """

        if self._category_editor is not None:  # Return editor lists instead of plain lists if it's enabled.
            return self._category_editor.get_lists()

        from .toolbox import get_category_lists
        init_kwargs = init_kwargs or {}

        catlist_kwargs = {}
        if self._category_lists_init_kwargs is not None:
            catlist_kwargs.update(self._category_lists_init_kwargs)
        catlist_kwargs.update(init_kwargs)

        lists = get_category_lists(catlist_kwargs, additional_parents_aliases, obj=self)

        return lists

    def enable_category_lists_editor(self, request, editor_init_kwargs=None, additional_parents_aliases=None,
                                     lists_init_kwargs=None, handler_init_kwargs=None):
        """Enables editor functionality for categories of this object.

        :param Request request: Django request object
        :param dict|None editor_init_kwargs: Keyword args to initialize category lists editor with.
            See CategoryList.enable_editor()
        :param list|None additional_parents_aliases: Aliases of categories for editor to render
            even if this object has no tie to them.
        :param dict|None lists_init_kwargs: Keyword args to initialize CategoryList objects with
        :param dict|None handler_init_kwargs: Keyword args to initialize CategoryRequestHandler object with
        :return:
        """
        from .toolbox import CategoryRequestHandler
        additional_parents_aliases = additional_parents_aliases or []
        lists_init_kwargs = lists_init_kwargs or {}
        editor_init_kwargs = editor_init_kwargs or {}
        handler_init_kwargs = handler_init_kwargs or {}
        handler = CategoryRequestHandler(request, self, **handler_init_kwargs)
        lists = self.get_category_lists(
            init_kwargs=lists_init_kwargs, additional_parents_aliases=additional_parents_aliases)
        handler.register_lists(lists, lists_init_kwargs=lists_init_kwargs, editor_init_kwargs=editor_init_kwargs)
        self._category_editor = handler  # Set link to handler to mutate get_category_lists() behaviour.
        return handler.listen()

    def add_to_category(self, category, user):
        """Add this model instance to a category.

        :param Category category: Category to add this object to
        :param User user: User heir who adds
        :return:
        """
        init_kwargs = {
            'category': category,
            'creator': user,
            'linked_object': self
        }
        tie = self.categories.model(**init_kwargs)  # That's a model of Tie.
        tie.save()
        return tie

    def remove_from_category(self, category):
        """Removes this object from a given category.

        :param Category category:
        :return:
        """
        ctype = ContentType.objects.get_for_model(self)
        self.categories.model.objects.filter(category=category, content_type=ctype, object_id=self.id).delete()

    @classmethod
    def get_ties_for_categories_qs(cls, categories, user=None, status=None):
        """Returns a QuerySet of Ties for the given categories.

        :param list|Category categories:
        :param User|None user:
        :param int|None status:
        :return:
        """
        if not isinstance(categories, list):
            categories = [categories]

        category_ids = []
        for category in categories:
            if isinstance(category, models.Model):
                category_ids.append(category.id)
            else:
                category_ids.append(category)
        filter_kwargs = {
            'content_type': ContentType.objects.get_for_model(cls, for_concrete_model=False),
            'category_id__in': category_ids
        }
        if user is not None:
            filter_kwargs['creator'] = user
        if status is not None:
            filter_kwargs['status'] = status
        ties = get_tie_model().objects.filter(**filter_kwargs)
        return ties

    @classmethod
    def get_from_category_qs(cls, category):
        """Returns a QuerySet of objects of this type associated with the given category.

        :param Category category:
        :rtype: list
        :return:
        """
        ids = cls.get_ties_for_categories_qs(category).values_list('object_id').distinct()
        filter_kwargs = {'id__in': [i[0] for i in ids]}
        return cls.objects.filter(**filter_kwargs)
