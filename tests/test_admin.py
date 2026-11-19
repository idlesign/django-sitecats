from django.contrib import admin as django_admin

from sitecats.models import Category


class TestAdmin:

    def test_changelists(self, admin_client, user, create_article, create_category):
        cat = create_category()

        article = create_article()
        article.add_to_category(cat, user)

        admin_client.configure(app='sitecats', model='category')
        assert admin_client.call_listing().ok

        admin_client.configure(app='sitecats', model='tie')
        assert admin_client.call_listing().ok

    def test_category_admin_locks(self, user_create, create_category, request_get):
        cat_locked = create_category(is_locked=True)
        cat_normal = create_category()

        model_admin = django_admin.site._registry[Category]
        request = request_get('/', user=user_create(superuser=True))

        assert not model_admin.has_delete_permission(request, obj=cat_locked)
        assert model_admin.has_delete_permission(request, obj=cat_normal)

        model_admin.get_form(request, obj=cat_locked)
        assert model_admin.readonly_fields == ('is_locked', 'alias')

        model_admin.get_form(request, obj=cat_normal)
        assert model_admin.readonly_fields == ()
