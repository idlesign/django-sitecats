Additional functionality via JS
===============================

**sitecats** bundles JS providing some additional functionality.

Do not forget to include JS file in your HTML to use it:

.. code-block:: html

    <script src="{{ STATIC_URL }}js/sitecats/sitecats.min.js"></script>


.. note::

    jQuery is required for **sitecats** client side functionality.



Rendering categories cloud
--------------------------

To convert your categories list into a cloud where category title font size depends upon a number

of items belonging to this category, use *make_cloud()* method.

.. code-block:: js

    // `article_categories` is an ID of HTML element containing categories lists.
    sitecats.make_cloud('article_categories');
