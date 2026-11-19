# Toolbox

Here are most important tools exposed by `sitecats`.

## Settings

You can override the following settings for your project:

* **SITECATS_MODEL_CATEGORY** — Path to a model to be used as a Category (e.g. `myapp.MyCategory`).

* **SITECATS_MODEL_TIE** — Path to a model to be used as a category-to-object Tie (e.g. `myapp.MyTie`).

## models

::: apidescribed: sitecats.models
    inherited: false
    only:
        - ModelWithCategory
        - TieBase

## toolbox

::: apidescribed: sitecats.toolbox
    only:
        - get_category_lists
        - get_category_aliases_under

## utils

::: apidescribed: sitecats.utils
    only:
        - get_category_model
        - get_tie_model
