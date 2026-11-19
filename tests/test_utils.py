from sitecats.utils import get_cache
from tests.testapp.models import Article


class TestCache:

    def test_sort_aliases_empty(self):
        assert get_cache().sort_aliases([]) == []

    def test_find_category(self, create_category):
        cat1 = create_category(alias='cat1')
        cat11 = create_category(parent=cat1, title='Child One')

        assert get_cache().find_category('cat1', 'child one') == cat11
        assert get_cache().find_category('cat1', 'no such') is None

    def test_get_ties_stats(self, user, create_article, create_category):
        cat = create_category()

        article = create_article()
        article.add_to_category(cat, user)

        stats = get_cache().get_ties_stats([cat.id], Article)
        assert stats == {cat.id: 1}

        stats = get_cache().get_ties_stats([cat.id], article)
        assert stats == {cat.id: 1}
