import pytest

from sitecats.exceptions import SitecatsConfigurationError, SitecatsSecurityException
from sitecats.models import Category
from sitecats.toolbox import CategoryList, CategoryRequestHandler, get_category_aliases_under
from tests.testapp.models import Article


class TestToolbox:

    def test_get_category_aliases_under(self, create_category):
        cat1 = create_category(alias='cat1',)
        create_category(alias='cat2',)
        create_category(alias='cat3')

        create_category(alias='cat11', parent=cat1)
        create_category(parent=cat1)

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
        assert not self.cl_cat1.show_links

        # test_show_title
        assert not self.cl.show_title
        assert self.cl_cat1.show_title

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


class TestCategoryRequestHandler:

    @pytest.fixture
    def setup(self, user, create_article, create_category):
        self.user = user
        self.cat1 = create_category(alias='cat1')
        self.cat11 = create_category(parent=self.cat1, title='child1')
        self.article = create_article()

    def get_handler(self, request_post, data=None, obj=None, editor_init_kwargs=None):
        handler = CategoryRequestHandler(request_post('/', data=data or {}, user=self.user), obj)
        handler.register_lists(['cat1'], editor_init_kwargs=editor_init_kwargs or {})
        return handler

    def test_register_lists_invalid(self, request_post):
        handler = CategoryRequestHandler(request_post('/'))

        with pytest.raises(SitecatsConfigurationError, match='accepts only'):
            handler.register_lists([object()])

    def test_register_lists_init_kwargs(self, create_category, request_post):
        create_category(alias='cat1')

        handler = CategoryRequestHandler(request_post('/'))
        handler.register_lists(['cat1'], lists_init_kwargs={'show_title': True})

        assert handler.get_lists()[0].show_title

    def test_listen_unknown_action(self, setup, request_post):
        handler = self.get_handler(request_post, data={'category_action': 'bogus'})

        with pytest.raises(SitecatsSecurityException, match='Unknown `category_action`'):
            handler.listen()

    def test_listen_unknown_base(self, setup, request_post):
        handler = self.get_handler(request_post, data={'category_action': 'add', 'category_base_id': '424242'})

        with pytest.raises(SitecatsSecurityException, match='Unknown `category_base_id`'):
            handler.listen()

    def test_listen_base_none(self, create_category, request_post):
        create_category(alias='cat1')

        handler = CategoryRequestHandler(
            request_post('/', data={'category_action': 'add', 'category_base_id': 'None', 'category_title': 'some'}))

        with pytest.raises(SitecatsSecurityException, match='Unknown `category_base_id`'):
            handler.listen()

    def test_listen_editor_disabled(self, setup, request_post):
        handler = CategoryRequestHandler(
            request_post('/', data={'category_action': 'add', 'category_base_id': str(self.cat1.id)}))

        catlist = CategoryList('cat1')
        handler._lists[catlist.get_id()] = catlist

        with pytest.raises(SitecatsSecurityException, match='Editor is disabled'):
            handler.listen()

    def test_action_add_tie(self, setup, request_post):
        data = {'category_action': 'add', 'category_base_id': str(self.cat1.id), 'category_title': 'child1'}

        handler = self.get_handler(request_post, data, obj=self.article, editor_init_kwargs={'max_num': 3})
        result = handler.listen()

        assert result == self.cat11
        assert len(Article.get_ties_for_categories_qs([self.cat11])) == 1

    def test_action_add_new_category(self, setup, request_post):
        data = {'category_action': 'add', 'category_base_id': str(self.cat1.id), 'category_title': 'brand new'}

        handler = self.get_handler(request_post, data, editor_init_kwargs={'allow_new': True})
        result = handler.listen()

        assert result.parent == self.cat1
        assert result.title == 'brand new'

    def test_action_add_existing_no_obj(self, setup, request_post):
        data = {'category_action': 'add', 'category_base_id': str(self.cat1.id), 'category_title': 'child1'}

        handler = self.get_handler(request_post, data, editor_init_kwargs={'max_num': 5})

        assert handler.listen() == self.cat11

    def test_action_add_new_forbidden(self, setup, request_post):
        data = {'category_action': 'add', 'category_base_id': str(self.cat1.id), 'category_title': 'brand new'}

        handler = self.get_handler(request_post, data)

        assert handler.listen() is None
        assert Category.objects.filter(title='brand new').count() == 0

    def test_action_add_max_num(self, setup, request_post):
        data = {'category_action': 'add', 'category_base_id': str(self.cat1.id), 'category_title': 'child1'}

        self.article.add_to_category(self.cat11, self.user)

        handler = self.get_handler(
            request_post, data, obj=self.article, editor_init_kwargs={'max_num': 1})

        assert handler.listen() is None

    def test_action_add_not_allowed(self, setup, request_post):
        data = {'category_action': 'add', 'category_base_id': str(self.cat1.id), 'category_title': 'child1'}

        handler = self.get_handler(request_post, data, obj=self.article, editor_init_kwargs={'allow_add': False})

        with pytest.raises(SitecatsSecurityException, match=r'`action_add\(\)` is not supported'):
            handler.listen()

    def test_action_add_empty_title(self, setup, request_post):
        data = {'category_action': 'add', 'category_base_id': str(self.cat1.id), 'category_title': '  '}

        handler = self.get_handler(request_post, data, obj=self.article)

        with pytest.raises(SitecatsSecurityException, match='Unsupported `category_title`'):
            handler.listen()

    def test_action_add_separator(self, setup, request_post):
        data = {
            'category_action': 'add',
            'category_base_id': str(self.cat1.id),
            'category_title': 'child1, another',
        }

        handler = self.get_handler(
            request_post, data, obj=self.article,
            editor_init_kwargs={'allow_new': True, 'category_separator': ','})
        result = handler.listen()

        assert result.title == 'another'
        assert len(Article.get_ties_for_categories_qs([self.cat11])) == 1
        assert len(Article.get_ties_for_categories_qs([result])) == 1

    def test_action_remove(self, setup, request_post):
        self.article.add_to_category(self.cat11, self.user)

        data = {
            'category_action': 'remove',
            'category_base_id': str(self.cat1.id),
            'category_id': str(self.cat11.id),
        }

        handler = self.get_handler(request_post, data, obj=self.article, editor_init_kwargs={'allow_remove': True})

        assert handler.listen() is True
        assert len(Article.get_ties_for_categories_qs([self.cat11])) == 0

    def test_action_remove_category_itself(self, setup, request_post):
        data = {
            'category_action': 'remove',
            'category_base_id': str(self.cat1.id),
            'category_id': str(self.cat11.id),
        }

        handler = self.get_handler(request_post, data, editor_init_kwargs={'allow_remove': True})

        assert handler.listen() is True
        assert Category.objects.filter(pk=self.cat11.pk).count() == 0

    def test_action_remove_min_num(self, setup, request_post):
        self.article.add_to_category(self.cat11, self.user)

        data = {
            'category_action': 'remove',
            'category_base_id': str(self.cat1.id),
            'category_id': str(self.cat11.id),
        }

        handler = self.get_handler(
            request_post, data, obj=self.article,
            editor_init_kwargs={'allow_remove': True, 'min_num': 1})

        assert handler.listen() is None
        assert len(Article.get_ties_for_categories_qs([self.cat11])) == 1

    def test_action_remove_not_allowed(self, setup, request_post):
        data = {'category_action': 'remove', 'category_base_id': str(self.cat1.id), 'category_id': '1'}

        handler = self.get_handler(request_post, data, obj=self.article, editor_init_kwargs={'allow_remove': False})

        with pytest.raises(SitecatsSecurityException, match=r'`action_remove\(\)` is not supported'):
            handler.listen()

    def test_action_remove_bad_category(self, setup, request_post, create_category):
        cat2 = create_category(alias='cat2')
        cat21 = create_category(parent=cat2)
        cat_locked = create_category(parent=self.cat1, is_locked=True)

        def get_handler_(category_id):
            data = {
                'category_action': 'remove',
                'category_base_id': str(self.cat1.id),
                'category_id': str(category_id),
            }
            return self.get_handler(request_post, data, editor_init_kwargs={'allow_remove': True})

        with pytest.raises(SitecatsSecurityException, match='Unsupported `category_id`'):
            get_handler_(0).listen()

        with pytest.raises(SitecatsSecurityException, match='Unable to get'):
            get_handler_(999999).listen()

        with pytest.raises(SitecatsSecurityException, match='not supported by'):
            get_handler_(cat_locked.id).listen()

        with pytest.raises(SitecatsSecurityException, match='not a child'):
            get_handler_(cat21.id).listen()
