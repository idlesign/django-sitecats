from django.db import models
from django.conf import settings
from django.utils import six
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import python_2_unicode_compatible
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from .settings import MODEL_CATEGORY, MODEL_FLAG
from .utils import get_flag_model, get_category_model


USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


# This allows South to handle our custom 'CharFieldNullable' field.
if 'south' in settings.INSTALLED_APPS:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ['^sitecats\.models\.CharFieldNullable'])


class CharFieldNullable(models.CharField):
    """We use custom char field to put nulls in CategoryBase 'alias' field.
    That allows 'unique' param to be handled properly, so we don't have
    two categories with the same alias.

    """
    def get_prep_value(self, value):
        if value is not None:
            if value.strip() == '':
                return None
        return self.to_python(value)


@python_2_unicode_compatible
class CategoryBase(models.Model):

    title = models.CharField(_('Title'), max_length=250, help_text=_('Category name.'))
    note = models.TextField(_('Note'), blank=True)

    alias = CharFieldNullable(_('Alias'), max_length=80, help_text=_('Short name to address category from a template.'), blank=True, null=True, unique=True)
    slug = models.SlugField(verbose_name=_('Slug'), unique=True, max_length=250, null=True, blank=True)
    status = models.IntegerField(_('Status'), help_text=_('.'), null=True, blank=True, db_index=True)

    creator = models.ForeignKey(USER_MODEL, related_name='%(class)s_creators', verbose_name=_('Creator'))
    time_created = models.DateTimeField(_('Date created'), auto_now_add=True)
    time_modified = models.DateTimeField(_('Date modified'), editable=False, auto_now=True)
    # The last two are for 'adjacency list' model.
    parent = models.ForeignKey('self', related_name='%(class)s_parents', verbose_name=_('Parent'), help_text=_('Parent category.'), db_index=True, null=True, blank=True)
    sort_order = models.PositiveIntegerField(_('Sort order'), help_text=_('Item position among other categories under the same parent.'), db_index=True, default=0)

    def get_href(self):
        return '#'  # TODO implement customized hrefs
    href = property(get_href)

    def save(self, force_insert=False, force_update=False, **kwargs):
        """We override parent save method to set category sort order to its primary key value."""
        super(CategoryBase, self).save(force_insert, force_update, **kwargs)
        if self.sort_order == 0:
            self.sort_order = self.id
            self.save()

    class Meta:
        abstract = True
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')

    def __str__(self):
        return self.title


@python_2_unicode_compatible
class FlagBase(models.Model):

    category = models.ForeignKey(MODEL_CATEGORY, related_name='%(class)s_categories', verbose_name=_('Category'), null=True, blank=True)
    note = models.TextField(_('Note'), blank=True)
    status = models.IntegerField(_('Status'), help_text=_('.'), null=True, blank=True, db_index=True)

    creator = models.ForeignKey(USER_MODEL, related_name='%(class)s_creators', verbose_name=_('Creator'))
    time_created = models.DateTimeField(_('Date created'), auto_now_add=True)

    # Here follows a link to an object.
    object_id = models.PositiveIntegerField(verbose_name=_('Object ID'), db_index=True)
    content_type = models.ForeignKey(ContentType, verbose_name=_('Content type'), related_name='%(app_label)s_%(class)s_tags')

    linked_object = generic.GenericForeignKey()

    class Meta:
        abstract = True
        verbose_name = _('Flag')
        verbose_name_plural = _('Flags')

    def __str__(self):
        return '%s:%s flagged %s' % (self.content_type, self.object_id, self.category)


class Category(CategoryBase):
    """Built-in category class. Default functionality."""


class Flag(FlagBase):
    """Built-in flag class. Default functionality."""


class ModelWithTag(models.Model):
    """Helper base class for models with tags."""

    tags = generic.GenericRelation(MODEL_FLAG)

    def get_tags(self):
        return self.tags.filter(category__isnull=False)

    def add_tag(self, tag, parent_category, user, note=''):
        parent_id = parent_category
        if isinstance(parent_category, models.Model):
            parent_id = parent_category.id
        category = get_category_model()(title=tag, creator=user, parent_id=parent_id)
        category.save()
        if isinstance(tag, six.string_types):
            tag = get_flag_model()(category=category, creator=user, note=note, linked_object=self)
        tag.save()
        return tag

    class Meta:
        abstract = True


class ModelWithBookmark(models.Model):
    """Helper base class for models with bookmarks."""

    bookmarks = generic.GenericRelation(MODEL_FLAG)

    def get_bookmarks(self):
        return self.bookmarks.filter(category__isnull=True)

    def add_bookmark(self, user, note=''):
        bookmark = get_flag_model()(category=None, creator=user, note=note, linked_object=self)
        bookmark.save()
        return bookmark

    def delete_bookmark(self, user):
        get_flag_model().objects.filter(category=None, creator=user, linked_object=self).delete()

    def is_bookmarked(self, user):
        if not user.id:
            return None
        return self.bookmarks.filter(category=None, creator=user).count()

    class Meta:
        abstract = True
