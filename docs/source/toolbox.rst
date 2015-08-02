Toolbox
=======

Here are tools exposed by ``sitecats``.


Settings
--------

You can override the following settings for your project:

* **SITECATS_MODEL_CATEGORY** - Path to a model to be used as a Category (e.g. `myapp.MyCategory`).

* **SITECATS_MODEL_TIE** - Path to a model to be used as a category-to-object Tie (e.g. `myapp.MyTie`).



get_category_model
------------------

.. autofunction:: sitecats.utils.get_category_model



get_tie_model
-------------

.. autofunction:: sitecats.utils.get_tie_model


Tie
---

Ties - are links between categories and various items of your site.

You can get tie model with `get_tie_model`.

Whether you need to know categories your site items are currently linked to alongside with ties themselves
you can use `get_linked_objects` method.

.. autoclass:: sitecats.models.Tie
    :members:


ModelWithCategory
-----------------

.. autoclass:: sitecats.models.ModelWithCategory
    :members:



get_category_lists
------------------

.. autofunction:: sitecats.toolbox.get_category_lists


get_category_aliases_under
--------------------------

.. autofunction:: sitecats.toolbox.get_category_aliases_under



CategoryList
------------

.. autoclass:: sitecats.toolbox.CategoryList
    :members:



CategoryRequestHandler
----------------------

.. autoclass:: sitecats.toolbox.CategoryRequestHandler
    :members:

