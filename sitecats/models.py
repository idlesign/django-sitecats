from django.core.urlresolvers import reverse
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
    title = models.CharField(_('Title'), max_length=250, help_text=_('Category name.'))
    alias = CharFieldNullable(_('Alias'), max_length=80, help_text=_('Short name to address category from a template.'), blank=True, null=True, unique=True)
    is_locked = models.BooleanField(_('Locked'), help_text=_('Categories used in application code are locked, their aliases are read only. Such categories can be deleted only from application code.'), default=False)

    parent = models.ForeignKey('self', related_name='%(class)s_parents', verbose_name=_('Parent'), help_text=_('Parent category.'), db_index=True, null=True, blank=True)
    note = models.TextField(_('Note'), blank=True)

    status = models.IntegerField(_('Status'), null=True, blank=True, db_index=True)
    slug = CharFieldNullable(verbose_name=_('Slug'), unique=True, max_length=250, null=True, blank=True)

    creator = models.ForeignKey(USER_MODEL, related_name='%(class)s_creators', verbose_name=_('Creator'))
    time_created = models.DateTimeField(_('Date created'), auto_now_add=True)
    time_modified = models.DateTimeField(_('Date modified'), editable=False, auto_now=True)

    sort_order = models.PositiveIntegerField(_('Sort order'), help_text=_('Item position among other categories under the same parent.'), db_index=True, default=0)

    class Meta:
        abstract = True
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')
        unique_together = ('title', 'parent')

    @classmethod
    def add(cls, title, creator, parent=None):
        obj = cls(title=title, creator=creator, parent=parent)
        obj.save()
        return obj

    def get_absolute_url(self, target_object=None):
        if target_object is not None and hasattr(target_object, 'get_category_absolute_url'):
            return lambda: target_object.get_category_absolute_url(self)
        return reverse('sitecats-listing', args=[str(self.id)])  # TODO think over

    def delete(self, *args, **kwargs):
        if self.is_locked:
            raise SitecatsLockedCategoryDelete('Unable to delete locked `%s` category.' % self)
        super(CategoryBase, self).delete(*args, **kwargs)

    def save(self, force_insert=False, force_update=False, **kwargs):
        """We override parent save method to set category sort order to its primary key value."""
        self.title = self.title.strip()
        super(CategoryBase, self).save(force_insert, force_update, **kwargs)
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
    content_type = models.ForeignKey(ContentType, verbose_name=_('Content type'), related_name='%(app_label)s_%(class)s_tags')

    linked_object = generic.GenericForeignKey()

    class Meta:
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
    """Helper base class for models with tags.

    Inherit from this model to be able to categorize model instances.

    """
    categories = generic.GenericRelation(MODEL_TIE)

    class Meta:
        abstract = True

    # TODO current categories lists shortcut method.

    def add_to_category(self, category, creator):
        init_kwargs = {
            'category': category,
            'creator': creator,
            'linked_object': self
        }
        tie = self.categories.model(**init_kwargs)
        tie.save()
        return tie

    def remove_from_category(self, category):
        ctype = ContentType.objects.get_for_model(self)
        self.categories.model.objects.filter(category=category, content_type=ctype, object_id=self.id).delete()

    @classmethod
    def get_ties_for_categories_qs(cls, categories, creator=None, status=None):
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
        if creator is not None:
            filter_kwargs['creator'] = creator
        if status is not None:
            filter_kwargs['status'] = status
        ties = get_tie_model().objects.filter(**filter_kwargs)
        return ties

    @classmethod
    def get_for_category(cls, category):
        ids = cls.get_ties_for_categories_qs(category).values_list('object_id').distinct()
        filter_kwargs = {'id__in': [i[0] for i in ids]}
        return cls.objects.filter(**filter_kwargs)
