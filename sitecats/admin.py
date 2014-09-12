from django.contrib import admin

from .utils import get_category_model, get_tie_model


try:
    from admirarchy.toolbox import HierarchicalModelAdmin
    MODEL_ADMIN = HierarchicalModelAdmin
except ImportError:
    MODEL_ADMIN = admin.ModelAdmin


class CategoryAdmin(MODEL_ADMIN):
    list_display = ('title', 'alias', 'is_locked', 'status')
    search_fields = ('title', 'alias', 'note', 'creator')
    list_filter = ('time_created', 'status')
    ordering = ('sort_order',)
    date_hierarchy = 'time_created'
    hierarchy = True

    def has_delete_permission(self, request, obj=None):
        if obj is not None and obj.is_locked:
            return False
        return super(CategoryAdmin, self).has_delete_permission(request, obj=obj)

    def get_form(self, request, obj=None, **kwargs):
        if obj is not None:
            if obj.is_locked:
                self.readonly_fields = ('is_locked', 'alias')
            else:
                self.readonly_fields = ()
        return super(CategoryAdmin, self).get_form(request, obj=obj, **kwargs)

admin.site.register(get_category_model(), CategoryAdmin)


class TieAdmin(admin.ModelAdmin):
    list_display = ('category', 'content_type', 'object_id', 'status')
    search_fields = ('object_id', 'content_type', 'creator')
    list_filter = ('time_created', 'status', 'content_type')
    ordering = ('-time_created',)
    date_hierarchy = 'time_created'

admin.site.register(get_tie_model(), TieAdmin)
