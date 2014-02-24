from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import python_2_unicode_compatible
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from .settings import MODEL_CATEGORY, MODEL_TAG


USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


# This allows South to handle our custom 'CharFieldNullable' field.
if 'south' in settings.INSTALLED_APPS:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ['^sitetcats\.models\.CharFieldNullable'])


class CharFieldNullable(models.CharField):
    """We use custom char field to put nulls in SiteTreeItem 'alias' field.
    That allows 'unique_together' directive in Meta to work properly, so
    we don't have two site tree items with the same alias in the same site tree.

    """
    def get_prep_value(self, value):
        if value is not None:
            if value.strip() == '':
                return None
        return self.to_python(value)


@python_2_unicode_compatible
class CategoryBase(models.Model):

    STATUS_NOT_SET = 0

    def get_status_choices(self):
        statuses = [
            (_('Basic'), (
                (self.STATUS_NOT_SET, _('Not set')),
            )),
        ]
        return statuses

    title = models.CharField(_('Title'), max_length=250, help_text=_('Category name.'))

    alias = CharFieldNullable(_('Alias'), max_length=80, help_text=_('Short name to address category from a template.'), blank=True, null=True, unique=True)
    slug = models.SlugField(verbose_name=_('Slug'), unique=True, max_length=250)
    status = models.IntegerField(_('Status'), help_text=_('.'), choices=get_status_choices(), default=STATUS_NOT_SET)

    creator = models.ForeignKey(USER_MODEL, related_name='creators', verbose_name=_('Creator'))
    time_created = models.DateTimeField(_('Date created'), auto_now_add=True)
    time_midified = models.DateTimeField(_('Date modified'), editable=False, auto_now=True)
    # The last two are for 'adjacency list' model.
    parent = models.ForeignKey('self', related_name='%(class)s_parent', verbose_name=_('Parent'), help_text=_('Parent category.'), db_index=True, null=True, blank=True)
    sort_order = models.IntegerField(_('Sort order'), help_text=_('Item position among other categories under the same parent.'), db_index=True, default=0)

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
class TagBase(models.Model):

    time_created = models.DateTimeField(_('Date created'), auto_now_add=True)
    category = models.ForeignKey(MODEL_CATEGORY, related_name='categories', verbose_name=_('Category'))
    creator = models.ForeignKey(USER_MODEL, related_name='creators', verbose_name=_('Creator'))

    # Here follows link to an object.
    object_id = models.PositiveIntegerField(verbose_name=_('Object ID'), db_index=True)
    content_type = models.ForeignKey(ContentType, verbose_name=_('Content type'), related_name='%(app_label)s_%(class)s_tags')

    linked_object = generic.GenericForeignKey()

    class Meta:
        abstract = True
        verbose_name = _('Tag')
        verbose_name_plural = _('Tags')

    def __str__(self):
        return _('%s:%s tagged %s' % (self.content_type, self.object_id, self.category))


class Category(CategoryBase):
    """Built-in category class. Default functionality."""


class Tag(TagBase):
    """Built-in tag class. Default functionality."""
