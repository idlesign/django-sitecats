from uuid import uuid4

from django.test import TestCase
from django.db import models
from django.contrib.auth.models import User
from django.db.utils import IntegrityError

from .models import Category, Tie, ModelWithCategory
from .exceptions import SitecatsLockedCategoryDelete
from .toolbox import CategoryList, CategoryRequestHandler, get_category_aliases_under


# TODO These two models creation will fail on Django 1.7, if migration dir is detected. What a mess!

class Comment(ModelWithCategory):

    title = models.CharField('title', max_length=255)


class Article(ModelWithCategory):

    title = models.CharField('title', max_length=255)


def create_comment():
    comment = Comment(title='comment%s' % uuid4().hex)
    comment.save()
    return comment


def create_article():
    article = Article(title='article%s' % uuid4().hex)
    article.save()
    return article


def create_user():
    user = User(username='user%s' % uuid4().hex)
    user.save()
    return user


def create_category(title=None, alias=None, parent=None, creator=None, **kwargs):
    if title is None:
        title = 'cat%s' % uuid4().hex
    if creator is None:
        creator = create_user()
    cat = Category(title=title, alias=alias, parent=parent, creator=creator, **kwargs)
    cat.save()
    return cat


class CategoryModelTest(TestCase):

    def test_alias_unique(self):
        create_category(alias='doubled')
        self.assertRaises(IntegrityError, create_category, None, 'doubled')

    def test_title_unique_in_parent(self):
        cat1 = create_category('title1')
        create_category('title1', parent=cat1)
        self.assertRaises(IntegrityError, create_category, 'title1', None, cat1)

    def test_delete(self):
        cat1 = create_category()
        cat1.delete()
        self.assertTrue(True)

        cat2 = create_category(is_locked=True)
        self.assertRaises(SitecatsLockedCategoryDelete, cat2.delete)

        cat2.is_locked = False
        cat2.delete()
        self.assertTrue(True)

    def test_add(self):
        user = create_user()
        cat1 = Category.add('new', user)

        self.assertIsNotNone(cat1.pk)
        self.assertEqual(cat1.creator, user)

        parent_cat = create_category()
        cat2 = Category.add('newest', user, parent=parent_cat)

        self.assertIsNotNone(cat2.pk)
        self.assertEqual(cat2.creator, user)
        self.assertEqual(cat2.parent, parent_cat)

    def test_sort_order(self):
        cat1 = create_category()
        self.assertEqual(cat1.sort_order, cat1.pk)

        cat2 = create_category(sort_order=128)
        self.assertEqual(cat2.sort_order, 128)

    def test_strip_title(self):
        cat1 = create_category(' my title ')
        self.assertEqual(cat1.title, 'my title')


class ModelWithCategoryTest(TestCase):

    # TODO set_category_lists_init_kwargs, get_category_lists, enable_category_lists_editor

    def test_add_to_category(self):
        user = create_user()
        cat = create_category()

        article = create_article()
        tie = article.add_to_category(cat, user)

        self.assertIsInstance(tie, Tie)
        self.assertEqual(tie.category, cat)
        self.assertEqual(tie.creator, user)

    def test_remove_from_category(self):
        user = create_user()
        cat = create_category()

        article = create_article()
        article.add_to_category(cat, user)

        ties = Article.get_ties_for_categories_qs([cat])
        self.assertEqual(len(ties), 1)

        article.remove_from_category(cat)
        ties = Article.get_ties_for_categories_qs([cat])
        self.assertEqual(len(ties), 0)

    def test_get_ties_for_categories_qs(self):

        user = create_user()
        user2 = create_user()
        cat1 = create_category()
        cat2 = create_category()

        article = create_article()
        tie1 = article.add_to_category(cat1, user)
        tie2 = article.add_to_category(cat2, user2)

        ties = Article.get_ties_for_categories_qs([cat1, cat2])

        self.assertEqual(len(ties), 2)
        self.assertIn(tie1, ties)
        self.assertIn(tie2, ties)

        ties = Article.get_ties_for_categories_qs([cat1, cat2], user=user2)

        self.assertEqual(len(ties), 1)
        self.assertNotIn(tie1, ties)
        self.assertIn(tie2, ties)

    def test_get_from_category_qs(self):
        user = create_user()
        cat1 = create_category()

        article = create_article()
        comment = create_comment()

        article.add_to_category(cat1, user)
        comment.add_to_category(cat1, user)

        articles_in_cat = Article.get_from_category_qs(cat1)
        self.assertEqual(len(articles_in_cat), 1)
        self.assertIn(article, articles_in_cat)

        comments_in_cat = Comment.get_from_category_qs(cat1)
        self.assertEqual(len(comments_in_cat), 1)
        self.assertIn(comment, comments_in_cat)


class ToolboxTest(TestCase):

    def test_get_category_aliases_under(self):
        cat1 = create_category(alias='cat1',)
        cat2 = create_category(alias='cat2',)
        cat3 = create_category(alias='cat3')

        cat11 = create_category(alias='cat11', parent=cat1)
        cat111 = create_category(parent=cat1)

        root = get_category_aliases_under()
        self.assertEqual(len(root), 3)
        self.assertIn('cat1', root)
        self.assertIn('cat2', root)
        self.assertIn('cat3', root)

        under_cat1 = get_category_aliases_under('cat1')
        self.assertEqual(len(under_cat1), 1)
        self.assertIn('cat11', under_cat1)


class CategoryListBasicTest(TestCase):

    def setUp(self):
        self.user = create_user()

        self.cat1 = create_category(alias='cat1', creator=self.user, note='some_note')

        self.cl = CategoryList()
        self.cl_cat1 = CategoryList('cat1', show_title=True, show_links=False, cat_html_class='somecss')

    def test_str(self):
        self.assertEqual(str(self.cl), '')
        self.assertEqual(str(self.cl_cat1), 'cat1')

    def test_cat_html_class(self):
        self.assertEqual(self.cl.cat_html_class, '')
        self.assertEqual(self.cl_cat1.cat_html_class, 'somecss')

    def test_show_links(self):
        self.assertTrue(self.cl.show_links)
        self.assertEqual(self.cl_cat1.show_links, False)

    def test_show_title(self):
        self.assertFalse(self.cl.show_title)
        self.assertEqual(self.cl_cat1.show_title, True)

    def test_alias(self):
        self.assertIsNone(self.cl.alias)
        self.assertEqual(self.cl_cat1.alias, 'cat1')

    def test_get_category_model(self):
        self.assertIsNone(self.cl.get_category_model())
        self.assertEqual(self.cl_cat1.get_category_model(), self.cat1)

    def test_get_title(self):
        self.assertEqual(self.cl.get_title(), 'Categories')
        self.assertEqual(self.cl_cat1.get_title(), self.cat1.title)

    def test_get_id(self):
        self.assertIsNone(self.cl.get_id())
        self.assertEqual(self.cl_cat1.get_id(), self.cat1.id)

    def test_get_note(self):
        self.assertEqual(self.cl.get_note(), '')
        self.assertEqual(self.cl_cat1.get_note(), self.cat1.note)


class CategoryListNoObjTest(TestCase):

    def setUp(self):
        self.user = create_user()

        self.cat1 = create_category(alias='cat1', creator=self.user, note='some_note')
        self.cat2 = create_category(alias='cat2', creator=self.user)
        self.cat3 = create_category(alias='cat3')

        self.cat11 = create_category(parent=self.cat1, note='subnote')
        self.cat111 = create_category(parent=self.cat1)

        self.cl = CategoryList()
        self.cl_cat1 = CategoryList('cat1', show_title=True, show_links=False, cat_html_class='somecss')

    def test_get_choices(self):
        choices = self.cl.get_choices()
        self.assertEqual(len(choices), 3)
        self.assertIn(self.cat1, choices)
        self.assertIn(self.cat2, choices)
        self.assertIn(self.cat3, choices)

        choices = self.cl_cat1.get_choices()
        self.assertEqual(len(choices), 2)
        self.assertIn(self.cat11, choices)
        self.assertIn(self.cat111, choices)

    def test_get_categories(self):
        cats = self.cl.get_categories()
        self.assertEqual(len(cats), 3)
        self.assertIn(self.cat1, cats)
        self.assertIn(self.cat2, cats)
        self.assertIn(self.cat3, cats)

        cats = self.cl_cat1.get_categories()
        self.assertEqual(len(cats), 2)
        self.assertIn(self.cat11, cats)
        self.assertIn(self.cat111, cats)


class CategoryListWithObjTest(TestCase):

    def setUp(self):
        self.article = create_article()
        self.comment = create_comment()
        self.user = create_user()

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


    def test_get_choices(self):
        choices = self.cl.get_choices()
        self.assertEqual(len(choices), 3)
        self.assertIn(self.cat1, choices)
        self.assertIn(self.cat2, choices)
        self.assertIn(self.cat3, choices)

        choices = self.cl_cat1.get_choices()
        self.assertEqual(len(choices), 2)
        self.assertIn(self.cat11, choices)
        self.assertIn(self.cat111, choices)

    def test_get_categories(self):
        cats = self.cl.get_categories()
        self.assertEqual(len(cats), 2)
        self.assertIn(self.cat1, cats)
        self.assertNotIn(self.cat2, cats)
        self.assertIn(self.cat3, cats)

        cats = self.cl_cat1.get_categories()
        self.assertEqual(len(cats), 1)
        self.assertIn(self.cat11, cats)


# TODO CategoryRequestHandler
