from uuid import uuid4

import pytest
from pytest_djangoapp import configure_djangoapp_plugin

pytest_plugins = configure_djangoapp_plugin(admin_contrib=True)


@pytest.fixture
def create_comment():
    from tests.testapp.models import Comment

    def create_comment_():
        comment = Comment(title='comment%s' % uuid4().hex)
        comment.save()
        return comment

    return create_comment_


@pytest.fixture
def create_article():
    from tests.testapp.models import Article

    def create_article_():
        article = Article(title='article%s' % uuid4().hex)
        article.save()
        return article

    return create_article_


@pytest.fixture
def create_category(user_create):

    def create_category_(title=None, alias=None, parent=None, creator=None, **kwargs):
        from sitecats.models import Category

        title = title or 'cat%s' % uuid4().hex

        creator = creator or user_create()

        cat = Category(title=title, alias=alias, parent=parent, creator=creator, **kwargs)
        cat.save()

        return cat

    return create_category_
