import pytest
from django.db.utils import IntegrityError

from sitecats.exceptions import SitecatsLockedCategoryDelete
from sitecats.models import Category, Tie
from sitecats.toolbox import CategoryList, get_category_lists, get_tie_model
from tests.testapp.models import Article, Comment

MODEL_TIE = get_tie_model()


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

    def test_str(self, create_category):
        assert str(create_category('mytitle', alias='myalias')) == 'mytitle (myalias)'
        assert str(create_category('mytitle2')) == 'mytitle2'

    def test_nullable_char_field(self):
        field = Category._meta.get_field('alias')

        assert field.get_prep_value(None) is None
        assert field.get_prep_value('   ') is None
        assert field.get_prep_value(' some ') == ' some '

    def test_sort_order(self, create_category):
        cat1 = create_category()
        assert cat1.sort_order == cat1.pk

        cat2 = create_category(sort_order=128)
        assert cat2.sort_order == 128

    def test_strip_title(self, create_category):
        cat1 = create_category(' my title ')
        assert cat1.title == 'my title'


class TestTie:

    def test_str(self, user, create_article, create_category):
        cat = create_category()
        article = create_article()
        tie = article.add_to_category(cat, user)

        assert str(tie) == f'{tie.content_type}:{tie.object_id} tied to {cat}'

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

    def test_get_category_lists(self, user, create_article, create_category):
        cat1 = create_category(alias='cat1')
        cat11 = create_category(parent=cat1)

        article = create_article()
        article.add_to_category(cat11, user)

        lists = article.get_category_lists()

        assert len(lists) == 1
        catlist = lists[0]
        assert isinstance(catlist, CategoryList)
        assert catlist.alias == 'cat1'
        assert catlist.obj is article

        cat2 = create_category(alias='cat2')
        create_category(parent=cat2)

        lists = article.get_category_lists(additional_parents_aliases=['cat2'])

        assert len(lists) == 2

    def test_get_category_lists_init_kwargs(self, user, create_article, create_category):
        cat1 = create_category(alias='cat1')
        cat11 = create_category(parent=cat1)

        article = create_article()
        article.add_to_category(cat11, user)

        article.set_category_lists_init_kwargs({'show_title': True, 'template': 'custom_list_box.html'})

        catlist = article.get_category_lists()[0]

        assert catlist.show_title
        assert catlist.template == 'custom_list_box.html'

        # Call arguments take precedence over the preset ones.
        catlist = article.get_category_lists(init_kwargs={'show_title': False})[0]

        assert not catlist.show_title

    def test_get_category_lists_custom_cls(self, create_category):
        class CustomList(CategoryList):
            pass

        cat1 = create_category(alias='cat1')
        create_category(parent=cat1)

        lists = get_category_lists(additional_parents_aliases=['cat1'], list_cls=CustomList)

        assert len(lists) == 1
        assert isinstance(lists[0], CustomList)

    def test_enable_category_lists_editor(self, user, create_article, create_category, request_post):
        cat1 = create_category(alias='cat1')
        create_category(parent=cat1)

        article = create_article()

        result = article.enable_category_lists_editor(request_post('/'), additional_parents_aliases=['cat1'])

        assert result is None  # No editor actions in the request.

        editor = article._category_editor
        assert editor is not None

        lists = article.get_category_lists()

        assert lists == editor.get_lists()
        assert lists[0].editor.allow_add

    def test_add_to_category(self, user, create_article, create_category):
        cat = create_category()

        article = create_article()
        tie = article.add_to_category(cat, user)

        assert isinstance(tie, Tie)
        assert tie.category == cat
        assert tie.creator == user

        # Repeated adding returns the existing tie instead of creating a duplicate.
        tie_again = article.add_to_category(cat, user)

        assert tie_again.pk == tie.pk
        assert Tie.objects.count() == 1

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

    def test_get_ties_for_categories_qs_status(self, user, create_article, create_category):
        cat = create_category()

        article = create_article()
        tie = article.add_to_category(cat, user)

        assert len(Article.get_ties_for_categories_qs([cat], status=1)) == 0

        tie.status = 1
        tie.save()

        assert len(Article.get_ties_for_categories_qs([cat], status=1)) == 1

    def test_get_from_category_qs(self, user, create_article, create_comment, create_category, db_queries):
        cat1 = create_category()

        article = create_article()
        comment = create_comment()

        article.add_to_category(cat1, user)
        comment.add_to_category(cat1, user)

        with db_queries.scope(expect=1):
            articles_in_cat = list(Article.get_from_category_qs(cat1))

        assert len(articles_in_cat) == 1
        assert article in articles_in_cat

        with db_queries.scope(expect=1):
            comments_in_cat = list(Comment.get_from_category_qs(cat1))

        assert len(comments_in_cat) == 1
        assert comment in comments_in_cat
