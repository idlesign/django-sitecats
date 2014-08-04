from django import template

from ..sitecatsapp import SiteCats, SiteCatsError


sitecats = SiteCats()

register = template.Library()


@register.tag
def sitecats_categories(parser, token):
    """Parses sitecats_categories tag parameters.


        Supported notations:

        1. {% sitecats_categories from "my_category" %}

           Renders all the tags from `my_category` aliased category.

        2. {% sitecats_categories from "my_category" for obj %}

           Renders tags residing in `my_category` category associated with the given `obj` object.

        3. {% sitecats_categories from "my_category" for obj template "sitecats/my_cats.html" %}

           Renders tags using "sitecats/my_tags.html" template.


    """
    tokens = token.split_contents()
    use_template = detect_clause(parser, 'template', tokens)
    target_obj = detect_clause(parser, 'for', tokens)
    category = detect_clause(parser, 'from', tokens)

    tokens_num = len(tokens)

    if tokens_num in (1, 3, 5, 7):
        return sitecats_categoriesNode(category, target_obj, use_template)
    else:
        raise template.TemplateSyntaxError('`sitecats_categories` tag expects the following notation: {% sitecats_categories from "my_category" for obj template "sitecats/my_tags.html" %}.')


class sitecats_categoriesNode(template.Node):
    """Renders tags under the specified category."""

    def __init__(self, category, target_object, use_template):
        self.use_template = use_template
        self.target_object = target_object
        self.category = category

    def render(self, context):
        resolve = lambda arg: arg.resolve(context) if isinstance(arg, template.FilterExpression) else arg

        context.push()
        try:
            context['sitecats_categories'] = sitecats.get_categories(resolve(self.category), resolve(self.target_object))
        except SiteCatsError:
            raise SiteCatsError('Object from `sitecats_categories` tag `for` clause must be a model.')

        contents = template.loader.get_template(resolve(self.use_template or 'sitecats/cats.html')).render(context)

        context.pop()

        return contents


def detect_clause(parser, clause_name, tokens):
    """Helper function detects a certain clause in tag tokens list.
    Returns its value.

    """
    if clause_name in tokens:
        t_index = tokens.index(clause_name)
        clause_value = parser.compile_filter(tokens[t_index + 1])
        del tokens[t_index:t_index + 2]
    else:
        clause_value = None
    return clause_value
