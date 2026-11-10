from uuid import uuid4

import pytest
from django.db.utils import IntegrityError
from django.template.base import TemplateSyntaxError
from django.template.context import Context

from sitecats.exceptions import SitecatsLockedCategoryDelete, SitecatsConfigurationError
from sitecats.models import Category, Tie
from sitecats.settings import UNRESOLVED_URL_MARKER
from sitecats.toolbox import CategoryList, get_category_aliases_under, get_tie_model, \
    get_category_model

MODEL_TIE = get_tie_model()
MODEL_CATEGORY = get_category_model()

from sitecats.tests.testapp.models import Comment, Article


@pytest.fixture
def create_comment():
    from sitecats.tests.testapp.models import Comment

    def create_comment_():
        comment = Comment(title='comment%s' % uuid4().hex)
        comment.save()
        return comment

    return create_comment_


@pytest.fixture
def create_article():
    from sitecats.tests.testapp.models import Article

    def create_article_():
        article = Article(title='article%s' % uuid4().hex)
        article.save()
        return article

    return create_article_


@pytest.fixture
def create_category(user_create):

    def create_category_(title=None, alias=None, parent=None, creator=None, **kwargs):
        title = title or 'cat%s' % uuid4().hex

        creator = creator or user_create()

        cat = Category(title=title, alias=alias, parent=parent, creator=creator, **kwargs)
        cat.save()

        return cat

    return create_category_


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
        print(result)
        assert ('data-catid="%s"' % self.cat3.id) in result
        assert ('data-catid="%s"' % self.cat31.id) in result

        # testing list of CategoryList passed into `from` clause
        context = template_context({'my_categories_list': [self.cl_cat3]})
        result = template_render_tag('sitecats', 'sitecats_categories from my_categories_list', context)
        assert ('data-catid="%s"' % self.cat3.id) in result
        assert ('data-catid="%s"' % self.cat31.id) in result

        # testing unknown type passed into `from` clause
        context = template_context({'my_categories_list': object()})
        result = template_render_tag('sitecats', 'sitecats_categories from my_categories_list', context)
        assert result == ''

        settings.DEBUG = True

        with pytest.raises(SitecatsConfigurationError):
            context = template_context({'my_categories_list': object()})
            template_render_tag('sitecats', 'sitecats_categories from my_categories_list', context)


class TestCategoryModel:

    def test_alias_unique(self, create_category):
        create_category(alias='doubled')

        with pytest.raises(IntegrityError):
            create_category(None, 'doubled')

    def test_title_unique_in_parent(self, create_category):
        cat1 = create_category('title1')
        create_category('title1', parent=cat1)

        with pytest.raises(IntegrityError):
            create_category('title1', None, cat1)

    def test_delete(self, create_category):
        cat1 = create_category()
        cat1.delete()

        cat2 = create_category(is_locked=True)

        with pytest.raises(SitecatsLockedCategoryDelete):
            cat2.delete()

        cat2.is_locked = False
        cat2.delete()

    def test_add(self, user, create_category):
        cat1 = Category.add('new', user)

        assert cat1.pk is not None
        assert cat1.creator == user

        parent_cat = create_category()
        cat2 = Category.add('newest', user, parent=parent_cat)

        assert cat2.pk is not None
        assert cat2.creator == user
        assert cat2.parent == parent_cat

    def test_sort_order(self, create_category):
        cat1 = create_category()
        assert cat1.sort_order == cat1.pk

        cat2 = create_category(sort_order=128)
        assert cat2.sort_order == 128

    def test_strip_title(self, create_category):
        cat1 = create_category(' my title ')
        assert cat1.title == 'my title'


class TestTie:

    def test_get_linked_objects(self, user, create_article, create_comment, create_category):
        cat1 = create_category()
        cat2 = create_category()
        cat3 = create_category()

        article1 = create_article()
        article2 = create_article()
        article3 = create_article()

        article1.add_to_category(cat1, user)
        article2.add_to_category(cat1, user)
        article3.add_to_category(cat1, user)
        article2.add_to_category(cat2, user)
        article3.add_to_category(cat3, user)

        linked = MODEL_TIE.get_linked_objects()
        keys = linked.keys()
        assert Article in keys
        assert Comment not in keys

        assert article1 in linked[Article]
        assert article2 in linked[Article]
        assert article3 in linked[Article]

        comment1 = create_comment()
        comment1.add_to_category(cat1, user)

        linked = MODEL_TIE.get_linked_objects()
        keys = linked.keys()
        assert Article in keys
        assert Comment in keys

        assert comment1 in linked[Comment]

        # testing `id_only`
        linked = MODEL_TIE.get_linked_objects(id_only=True)
        assert article1.id in linked[Article]
        assert article2.id in linked[Article]
        assert article3.id in linked[Article]
        assert comment1.id in linked[Comment]

        # testing `by_category`
        linked = MODEL_TIE.get_linked_objects(by_category=True)
        keys = linked.keys()
        assert cat1 in keys
        assert cat2 in keys
        assert cat3 in keys

        assert len(linked[cat1]) == 2  # Article + Comment
        assert len(linked[cat2]) == 1
        assert len(linked[cat3]) == 1


class TestModelWithCategory:

    # TODO set_category_lists_init_kwargs, get_category_lists, enable_category_lists_editor

    def test_add_to_category(self, user, create_article, create_category):
        cat = create_category()

        article = create_article()
        tie = article.add_to_category(cat, user)

        assert isinstance(tie, Tie)
        assert tie.category == cat
        assert tie.creator == user

    def test_remove_from_category(self, user, create_article, create_category):
        cat = create_category()

        article = create_article()
        article.add_to_category(cat, user)

        ties = Article.get_ties_for_categories_qs([cat])
        assert len(ties) == 1

        article.remove_from_category(cat)
        ties = Article.get_ties_for_categories_qs([cat])
        assert len(ties) == 0

    def test_get_ties_for_categories_qs(self, user_create, create_article, create_category):

        user = user_create()
        user2 = user_create()
        cat1 = create_category()
        cat2 = create_category()

        article = create_article()
        tie1 = article.add_to_category(cat1, user)
        tie2 = article.add_to_category(cat2, user2)

        ties = Article.get_ties_for_categories_qs([cat1, cat2])

        assert len(ties) == 2
        assert tie1 in ties
        assert tie2 in ties

        ties = Article.get_ties_for_categories_qs([cat1, cat2], user=user2)

        assert len(ties) == 1
        assert tie1 not in ties
        assert tie2 in ties

    def test_get_from_category_qs(self, user, create_article, create_comment, create_category):
        cat1 = create_category()

        article = create_article()
        comment = create_comment()

        article.add_to_category(cat1, user)
        comment.add_to_category(cat1, user)

        articles_in_cat = Article.get_from_category_qs(cat1)
        assert len(articles_in_cat) == 1
        assert article in articles_in_cat

        comments_in_cat = Comment.get_from_category_qs(cat1)
        assert len(comments_in_cat) == 1
        assert comment in comments_in_cat


class TestToolbox:

    def test_get_category_aliases_under(self, create_category):
        cat1 = create_category(alias='cat1',)
        cat2 = create_category(alias='cat2',)
        cat3 = create_category(alias='cat3')

        cat11 = create_category(alias='cat11', parent=cat1)
        cat111 = create_category(parent=cat1)

        root = get_category_aliases_under()
        assert len(root) == 3
        assert 'cat1' in root
        assert 'cat2' in root
        assert 'cat3' in root

        under_cat1 = get_category_aliases_under('cat1')
        assert len(under_cat1) == 1
        assert 'cat11' in under_cat1


class TestCategoryListBasic:

    @pytest.fixture
    def setup(self, user, create_category):
        self.user = user

        self.cat1 = create_category(alias='cat1', creator=self.user, note='some_note')

        self.cl = CategoryList()
        self.cl_cat1 = CategoryList('cat1', show_title=True, show_links=False, cat_html_class='somecss')

    def test_all(self, setup):
        assert str(self.cl) == ''
        assert str(self.cl_cat1) == 'cat1'

        # test_cat_html_class
        assert self.cl.cat_html_class == ''
        assert self.cl_cat1.cat_html_class == 'somecss'

        # test_show_links
        assert self.cl.show_links
        assert self.cl_cat1.show_links == False

        # test_show_title
        assert not self.cl.show_title
        assert self.cl_cat1.show_title == True

        # test_alias
        assert self.cl.alias is None
        assert self.cl_cat1.alias == 'cat1'

        # test_get_category_model
        assert self.cl.get_category_model() is None
        assert self.cl_cat1.get_category_model() == self.cat1

        # test_get_title
        assert self.cl.get_title() == 'Categories'
        assert self.cl_cat1.get_title() == self.cat1.title

        # test_get_id
        assert self.cl.get_id() is None
        assert self.cl_cat1.get_id() == self.cat1.id

        # test_get_note
        assert self.cl.get_note() == ''
        assert self.cl_cat1.get_note() == self.cat1.note


class TestCategoryListNoObj:

    @pytest.fixture
    def setup(self, user, create_category):
        self.user = user

        self.cat1 = create_category(alias='cat1', creator=self.user, note='some_note')
        self.cat2 = create_category(alias='cat2', creator=self.user)
        self.cat3 = create_category(alias='cat3')

        self.cat11 = create_category(parent=self.cat1, note='subnote')
        self.cat111 = create_category(parent=self.cat1)

        self.cl = CategoryList()
        self.cl_cat1 = CategoryList('cat1', show_title=True, show_links=False, cat_html_class='somecss')

    def test_all(self, setup):
        # test_get_choices
        choices = self.cl.get_choices()
        assert len(choices) == 3
        assert self.cat1 in choices
        assert self.cat2 in choices
        assert self.cat3 in choices

        choices = self.cl_cat1.get_choices()
        assert len(choices) == 2
        assert self.cat11 in choices
        assert self.cat111 in choices

        # test_get_categories
        cats = self.cl.get_categories()
        assert len(cats) == 3
        assert self.cat1 in cats
        assert self.cat2 in cats
        assert self.cat3 in cats

        cats = self.cl_cat1.get_categories()
        assert len(cats) == 2
        assert self.cat11 in cats
        assert self.cat111 in cats


class TestCategoryListWithObj:

    @pytest.fixture
    def setup(self, user, create_article, create_comment, create_category):
        self.article = create_article()
        self.comment = create_comment()
        self.user = user

        self.cat1 = create_category(alias='cat1', creator=self.user, note='some_note')
        self.cat2 = create_category(alias='cat2', creator=self.user)
        self.cat3 = create_category(alias='cat3')

        self.cat11 = create_category(parent=self.cat1, note='subnote')
        self.cat111 = create_category(parent=self.cat1)

        self.cat22 = create_category(parent=self.cat2)
        self.cat222 = create_category(parent=self.cat2)
        self.cat2222 = create_category(parent=self.cat2)

        self.article.add_to_category(self.cat1, self.user)
        self.article.add_to_category(self.cat11, self.user)
        self.article.add_to_category(self.cat3, self.user)

        self.comment.add_to_category(self.cat1, self.user)
        self.comment.add_to_category(self.cat111, self.user)
        self.comment.add_to_category(self.cat2, self.user)
        self.comment.add_to_category(self.cat3, self.user)

        self.cl = CategoryList()
        self.cl.set_obj(self.article)
        self.cl_cat1 = CategoryList('cat1', show_title=True, show_links=False, cat_html_class='somecss')
        self.cl_cat1.set_obj(self.article)

    def test_all(self, setup):
        # test_get_choices
        choices = self.cl.get_choices()
        assert len(choices) == 3
        assert self.cat1 in choices
        assert self.cat2 in choices
        assert self.cat3 in choices

        choices = self.cl_cat1.get_choices()
        assert len(choices) == 2
        assert self.cat11 in choices
        assert self.cat111 in choices

        # test_get_categories
        cats = self.cl.get_categories()
        assert len(cats) == 2
        assert self.cat1 in cats
        assert self.cat2 not in cats
        assert self.cat3 in cats

        cats = self.cl_cat1.get_categories()
        assert len(cats) == 1
        assert self.cat11 in cats


# TODO CategoryRequestHandler
