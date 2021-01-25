django-sitecats
===============
https://github.com/idlesign/django-sitecats

.. image:: https://img.shields.io/pypi/v/django-sitecats.svg
    :target: https://pypi.python.org/pypi/django-sitecats

.. image:: https://img.shields.io/pypi/l/django-sitecats.svg
    :target: https://pypi.python.org/pypi/django-sitecats

.. image:: https://img.shields.io/coveralls/idlesign/django-sitecats/master.svg
    :target: https://coveralls.io/r/idlesign/django-sitecats

.. image:: https://img.shields.io/travis/idlesign/django-sitecats/master.svg
    :target: https://travis-ci.org/idlesign/django-sitecats


Description
-----------

*Django reusable application for content categorization.*

Nay, - you say, - all that tags business lacks structuring.

This application is just about structuring your data: build categories hierarchy and link your site entities to those categories.


.. code-block:: python

    # Somewhere in views.py
    from django.shortcuts import render, get_object_or_404

    # Suppose Article model has sitecats.models.ModelWithCategory class mixed in.
    from .models import Article


    def article_details(self, request, article_id):
        """See, there is nothing special in this view, yet it'll render a page with categories for the article."""
        return self.render(request, 'article.html', {'article': get_object_or_404(Article, pk=article_id)})

    def article_edit(self, request, article_id):
        """Let's allow this view to render and handle categories editor."""
        article = get_object_or_404(Article, pk=article_id)

        # Now we enable category editor for an article, and allow users
        # to add subcategories to `language`, and `os` categories
        # (suppose we created them beforehand with Admin contrib),
        # and link this article to them.
        article.enable_category_lists_editor(
            request,
            editor_init_kwargs={'allow_new': True},
            additional_parents_aliases=['language', 'os']
        )

        form = ... # Your usual Article edit handling code will be here.

        return render(request, 'article.html', {'article': article, 'form': form})



Template coding basically boils down to ``sitecats_categories`` template tags usage:

.. code-block:: html

    <!-- The same html is just fine for demonstration purposes for both our views.
         Do not forget to load `sitecats` template tags library. -->
    {% extends "base.html" %}
    {% load sitecats %}

    {% block contents %}
        <!-- Some additional functionality (e.g. categories cloud rendering,
             editor enhancements) will require JS. -->
        <script src="{{ STATIC_URL }}js/sitecats/sitecats.min.js"></script>

        <h1>{{ article.title }}</h1>
        <div id="article_categories">
            {% sitecats_categories from article %} <!-- And that's it. -->
        </div>
        <!-- Form code goes somewhere here. -->
    {% endblock %}


Read the docs, ``sitecats`` can do more.


Documentation
-------------

https://django-sitecats.readthedocs.org/
