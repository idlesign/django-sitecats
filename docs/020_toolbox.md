# Toolbox

Here are most important tools exposed by `sitecats`.

## Settings

You can override the following settings for your project:

* **SITECATS_MODEL_CATEGORY** — Path to a model to be used as a Category (e.g. `myapp.MyCategory`).

* **SITECATS_MODEL_TIE** — Path to a model to be used as a category-to-object Tie (e.g. `myapp.MyTie`).

## toolbox.get_category_model

Returns the Category model, set for the project.

Defaults to `models.Category`, can be customized by subclassing `models.CategoryBase`.

## toolbox.get_tie_model

Returns the Tie model, set for the project.

Defaults to `models.Tie`, can be customized by subclassing `models.TieBase`.

## models.TieBase

Base class for ties models.

Ties are relations between site entities and categories (see above).

Inherit from this model and override **SITECATS_MODEL_TIE** in *settings.py*
to customize model fields and behaviour.

You can get tie model with `get_tie_model`.

Whether you need to know categories your site items are currently linked to alongside with ties themselves
you can use `get_linked_objects` method.

### `get_linked_objects(cls, filter_kwargs=None, id_only=False, by_category=False)`

Returns objects linked to categories in a dictionary indexed by model classes.

* `dict filter_kwargs` — Filter for ties.
* `bool id_only` — If True only IDs of linked objects are returned, otherwise — QuerySets.
* `bool by_category` — If True only linked objects and their models a grouped by categories.

## models.ModelWithCategory

Helper class for models with tags.

Mix in this helper to your model class to be able to categorize model instances.

### `set_category_lists_init_kwargs(self, kwa_dict)`

Sets keyword arguments for category lists which can be spawned
by `get_categories()`.

* `dict|None kwa_dict`

### `enable_category_lists_editor(self, request, editor_init_kwargs=None, additional_parents_aliases=None, lists_init_kwargs=None, handler_init_kwargs=None)`

Enables editor functionality for categories of this object.

* `Request request` — Django request object
* `dict editor_init_kwargs` — Keyword args to initialize category lists editor with. See `CategoryList.enable_editor()`
* `list additional_parents_aliases` — Aliases of categories for editor to render even if this object has no tie to them.
* `dict lists_init_kwargs` — Keyword args to initialize CategoryList objects with
* `dict handler_init_kwargs` — Keyword args to initialize CategoryRequestHandler object with

### `add_to_category(self, category, user)`

Add this model instance to a category.

E.g: `my_article.add_to_category(category_one, request.user)`.

* `Category category` — Category to add this object to
* `User user` — User heir who adds

### `remove_from_category(self, category)`

Removes this object from a given category.

E.g: `my_article.remove_from_category(category_one)`.

* `Category category`

### `get_ties_for_categories_qs(cls, categories, user=None, status=None)`

Returns a QuerySet of Ties for the given categories.

E.g: `Article.get_ties_for_categories_qs([category_one, category_two])`.

* `list|Category categories`
* `User|None user`
* `int|None status`

### `get_from_category_qs(cls, category)`

Returns a QuerySet of objects of this type associated with the given category.

E.g: `Article.get_from_category_qs(my_category)`.

* `Category category`

## toolbox.get_category_lists

### `get_category_lists(init_kwargs=None, additional_parents_aliases=None, obj=None)`

Returns a list of CategoryList objects, optionally associated with
a given model instance.

* `dict|None init_kwargs`
* `list|None additional_parents_aliases`
* `Model|None obj` — Model instance to get categories for
* Returns: list

## toolbox.get_category_aliases_under

### `get_category_aliases_under(parent_alias=None)`

Returns a list of category aliases under the given parent.

Could be useful to pass to `ModelWithCategory.enable_category_lists_editor`
in `additional_parents_aliases` parameter.

* `str|None parent_alias` — Parent alias or None to categories under root
* Returns: list
