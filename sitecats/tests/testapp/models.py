from django.db import models

from sitecats.models import ModelWithCategory


class Comment(ModelWithCategory):

    title = models.CharField('title', max_length=255)


class Article(ModelWithCategory):

    title = models.CharField('title', max_length=255)

    def get_category_absolute_url(self, category):
        return '%s/%s' % (category.id, self.title)
