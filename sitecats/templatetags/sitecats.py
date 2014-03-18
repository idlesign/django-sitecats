from django import template

from ..utils import get_category_model

register = template.Library()


@register.tag
def sitecats_tags(parser, token):
    """Parses sitecats_tags tag parameters.


        Supported notations:

        1. {% sitecats_tags from "my_category" %}

           Renders all the tags from `my_category` aliased category.

        2. {% sitecats_tags from "my_category" for obj %}

           Renders tags residing in `my_category` category associated with the given `obj` object.

        3. {% sitecats_tags from "my_category" for obj template "sitecats/my_tags.html" %}

           Renders tags using "sitecats/my_tags.html" template.


    """
    tokens = token.split_contents()
    use_template = detect_clause(parser, 'template', tokens)
    target_obj = detect_clause(parser, 'for', tokens)

    tokens_num = len(tokens)

    if tokens_num in (3, 5, 7):
        category_alias = parser.compile_filter(tokens[2])
        return sitecats_tagsNode(category_alias, target_obj, use_template)
    else:
        raise template.TemplateSyntaxError('`sitecats_tags` tag expects the following notation: {% sitecats_tags from "my_category" for obj template "sitecats/my_tags.html" %}.')


class sitecats_tagsNode(template.Node):
    """Renders tags under the specified category."""

    def __init__(self, category_alias, target_object, use_template):
        self.use_template = use_template
        self.target_object = target_object
        self.category_alias = category_alias

    def render(self, context):
        use_template = self.use_template or 'sitecats/tags.html'

        if isinstance(use_template, template.FilterExpression):
            use_template = use_template.resolve(context)

        category_model = get_category_model()  # TODO implement

        context.push()
        context['sitecats_tags'] = []

        contents = template.loader.get_template(use_template).render(context)

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
