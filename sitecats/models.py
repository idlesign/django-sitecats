from django.core.urlresolvers import reverse
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
    """Base class for category models.

    Categories form a hierarchical registry to help structuring site entities.

    Inherit from this model and override SITECATS_MODEL_CATEGORY in settings.py
    to customize model fields and behaviour.

    """
    title = models.CharField(_('Title'), max_length=250, help_text=_('Category name.'))
    note = models.TextField(_('Note'), blank=True)

    alias = CharFieldNullable(_('Alias'), max_length=80, help_text=_('Short name to address category from a template.'), blank=True, null=True, unique=True)
    slug = models.SlugField(verbose_name=_('Slug'), unique=True, max_length=250, null=True, blank=True)
    status = models.IntegerField(_('Status'), null=True, blank=True, db_index=True)

    creator = models.ForeignKey(USER_MODEL, related_name='%(class)s_creators', verbose_name=_('Creator'))
    time_created = models.DateTimeField(_('Date created'), auto_now_add=True)
    time_modified = models.DateTimeField(_('Date modified'), editable=False, auto_now=True)
    # The last two are for 'adjacency list' model.
    parent = models.ForeignKey('self', related_name='%(class)s_parents', verbose_name=_('Parent'), help_text=_('Parent category.'), db_index=True, null=True, blank=True)
    sort_order = models.PositiveIntegerField(_('Sort order'), help_text=_('Item position among other categories under the same parent.'), db_index=True, default=0)

    def get_absolute_url(self, target_object=None):
        if target_object is not None and hasattr(target_object, 'get_category_absolute_url'):
            return lambda: target_object.get_category_absolute_url(self)
        return reverse('sitecats-listing', args=[str(self.id)])  # TODO think over

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
    """Base class for flag models.

    Flags are relations between site entities and categories (see above).

    Inherit from this model and override SITECATS_MODEL_FLAG in settings.py
    to customize model fields and behaviour.

    """
    category = models.ForeignKey(MODEL_CATEGORY, related_name='%(class)s_categories', verbose_name=_('Category'))
    note = models.TextField(_('Note'), blank=True)
    status = models.IntegerField(_('Status'), null=True, blank=True, db_index=True)

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


class ModelWithCategory(models.Model):
    """Helper base class for models with tags.

    Inherit from this model to be able to categorize model instances.

    """

    categories = generic.GenericRelation(MODEL_FLAG)

    def get_tags(self):
        return self.categories.filter(category__isnull=False)

    def categorize(self, category, parent_category, user, note=None):
        parent_id = parent_category
        if isinstance(parent_category, models.Model):
            parent_id = parent_category.id
        cat = get_category_model()(title=category, creator=user, parent_id=parent_id)
        cat.save()
        if isinstance(category, six.string_types):
            init_kwargs = {
                'category': cat,
                'creator': user,
                'linked_object': self
            }
            if note is not None:
                init_kwargs['note'] = note
            category = get_flag_model()(**init_kwargs)
        category.save()
        return category

    @classmethod
    def get_categorized(cls, filter_kwargs=None):
        # TODO caching
        ids = get_flag_model().objects.filter(content_type=ContentType.objects.get_for_model(cls)).values_list('object_id').distinct()
        kwargs = {'id__in': [i[0] for i in ids]}
        if filter_kwargs is not None:
            kwargs.update(filter_kwargs)
        return cls.objects.filter(**kwargs)

    @classmethod
    def _get_flag_relname(cls):
        return cls._meta.get_field_by_name('category')[0].rel.related_name

    class Meta:
        abstract = True

