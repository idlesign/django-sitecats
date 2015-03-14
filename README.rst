django-sitecats
===============
https://github.com/idlesign/django-sitecats


.. image:: https://badge.fury.io/py/django-sitecats.png
    :target: http://badge.fury.io/py/django-sitecats

.. image:: https://pypip.in/d/django-sitecats/badge.png
        :target: https://crate.io/packages/django-sitecats

.. image:: https://coveralls.io/repos/idlesign/django-sitecats/badge.png
    :target: https://coveralls.io/r/idlesign/django-sitecats

.. image:: https://travis-ci.org/idlesign/django-sitecats.svg?branch=master
    :target: https://travis-ci.org/idlesign/django-sitecats

.. image:: https://landscape.io/github/idlesign/django-sitecats/master/landscape.svg?style=plastic
   :target: https://landscape.io/github/idlesign/django-sitecats/master


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
        # not only to link that article to subcategories of `language`, and `os` categories,
        # but also to add those subcategories.
        article.enable_category_lists_editor(request,
                                editor_init_kwargs={'allow_new': True},
                                additional_parents_aliases=['language', 'os'])

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

http://django-sitecats.readthedocs.org/
