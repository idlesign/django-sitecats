import pytest
from django.template.base import TemplateSyntaxError

from sitecats.exceptions import SitecatsConfigurationError
from sitecats.settings import UNRESOLVED_URL_MARKER
from sitecats.toolbox import CategoryList


class TestTemplateTags:

    @pytest.fixture
    def setup(self, user, create_article, create_category):
        self.user = user

        self.cat1 = create_category(alias='cat1')
        self.cl_cat1 = CategoryList('cat1')

        self.cat2 = create_category(alias='cat2')
        self.cl_cat2 = CategoryList('cat2', show_links=lambda category: category.id)

        self.cat3 = create_category(alias='cat3')
        self.cat31 = create_category(alias='cat31', parent=self.cat3)
        self.cl_cat3 = CategoryList('cat3')

        self.art1 = create_article()

    def test_sitecats_url(self, setup, template_render_tag, template_context):

        with pytest.raises(TemplateSyntaxError):
            template_render_tag('sitecats', 'sitecats_url')

        # testing UNRESOLVED_URL_MARKER
        context = template_context({'my_category': self.cat1, 'my_list': self.cl_cat1})
        result = template_render_tag('sitecats', 'sitecats_url for my_category using my_list', context)
        assert result == UNRESOLVED_URL_MARKER

        # testing ModelWithCategory.get_category_absolute_url()
        self.cl_cat1.set_obj(self.art1)
        expected_url = '%s/%s' % (self.cat1.id, self.art1.title)
        assert template_render_tag('sitecats', 'sitecats_url for my_category using my_list', context) == expected_url

        template_render_tag('sitecats', 'sitecats_url for my_category using my_list as someurl', context)
        assert context.get('someurl') == expected_url

        # testing CategoryList.show_links
        context = template_context({'my_category': self.cat2, 'my_list': self.cl_cat2})
        result = template_render_tag('sitecats', 'sitecats_url for my_category using my_list', context)
        assert result == str(self.cat2.id)

    def test_sitecats_categories(self, setup, template_render_tag, template_context, settings):

        with pytest.raises(TemplateSyntaxError):
            template_render_tag('sitecats', 'sitecats_categories')

        # testing CategoryList passed into `from` clause
        context = template_context({'my_categories_list': self.cl_cat3})
        result = template_render_tag('sitecats', 'sitecats_categories from my_categories_list', context)
        assert ('data-catid="%s"' % self.cat3.id) in result
        assert ('data-catid="%s"' % self.cat31.id) in result

        # testing list of CategoryList passed into `from` clause
        context = template_context({'my_categories_list': [self.cl_cat3]})
        result = template_render_tag('sitecats', 'sitecats_categories from my_categories_list', context)
        assert ('data-catid="%s"' % self.cat3.id) in result
        assert ('data-catid="%s"' % self.cat31.id) in result

        # testing custom list template
        self.cl_cat3.template = 'custom_list_box.html'
        context = template_context({'my_categories_list': self.cl_cat3})
        result = template_render_tag('sitecats', 'sitecats_categories from my_categories_list', context)
        assert 'custom template marker: cat3' in result
        self.cl_cat3.template = None

        # testing unknown type passed into `from` clause
        context = template_context({'my_categories_list': object()})
        result = template_render_tag('sitecats', 'sitecats_categories from my_categories_list', context)
        assert result == ''

        settings.DEBUG = True

        context = template_context({'my_categories_list': object()})

        with pytest.raises(SitecatsConfigurationError):
            template_render_tag('sitecats', 'sitecats_categories from my_categories_list', context)

    def test_sitecats_categories_from_obj(self, user, create_article, create_category, request_post,
                                          template_render_tag, template_context):
        cat1 = create_category(alias='cat1')
        cat11 = create_category(parent=cat1)

        article = create_article()
        article.add_to_category(cat11, user)
        article.enable_category_lists_editor(
            request_post('/'),
            additional_parents_aliases=['cat1'],
            editor_init_kwargs={'allow_remove': True},
        )

        context = template_context({'my_obj': article})
        result = template_render_tag('sitecats', 'sitecats_categories from my_obj', context)

        assert result.count('<form id="catform_remove_') == 1
        assert 'name="category_id" value="%s"' % cat11.id in result
        assert 'data-catid="%s"' % cat11.id in result

    def test_sitecats_categories_from_handler(self, user, create_article, create_category, request_post,
                                              template_render_tag, template_context):
        cat1 = create_category(alias='cat1')
        cat11 = create_category(parent=cat1)

        article = create_article()
        article.add_to_category(cat11, user)
        article.enable_category_lists_editor(request_post('/'), additional_parents_aliases=['cat1'])

        context = template_context({'my_handler': article._category_editor})
        result = template_render_tag('sitecats', 'sitecats_categories from my_handler', context)

        assert result
