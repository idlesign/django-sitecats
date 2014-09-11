from django import template
from django.conf import settings

from ..models import ModelWithCategory
from ..toolbox import CategoryRequestHandler, CategoryList
from ..exceptions import SitecatsConfigurationError

register = template.Library()


@register.tag
def sitecats_categories(parser, token):
    tokens = token.split_contents()
    use_template = detect_clause(parser, 'template', tokens)
    target_obj = detect_clause(parser, 'from', tokens)

    tokens_num = len(tokens)

    if tokens_num in (1, 3):
        return sitecats_categoriesNode(target_obj, use_template)
    else:
        raise template.TemplateSyntaxError('`sitecats_categories` tag expects the following notation: {% sitecats_categories from my_categories_list template "sitecats/my_categories.html" %}.')


class sitecats_categoriesNode(template.Node):

    def __init__(self, target_obj, use_template):
        self.use_template = use_template
        self.target_obj = target_obj

    def render(self, context):
        resolve = lambda arg: arg.resolve(context) if isinstance(arg, template.FilterExpression) else arg

        target_obj = resolve(self.target_obj)
        if isinstance(target_obj, CategoryRequestHandler):
            target_obj = target_obj.get_lists()
        elif isinstance(target_obj, ModelWithCategory):
            target_obj = target_obj.get_category_lists()
        elif isinstance(target_obj, (list, tuple)):  # Simple list of CategotyList items.
            pass
        else:
            if isinstance(target_obj, CategoryList):
                target_obj = (target_obj,)
            else:
                if settings.DEBUG:
                    raise SitecatsConfigurationError('`sitecats_categories` template tag can\'t accept `%s` type from `%s` template variable.' % (type(target_obj), self.target_obj))
                return ''  # Silent fall.

        context.push()
        context['sitecats_categories'] = target_obj
        contents = template.loader.get_template(resolve(self.use_template or 'sitecats/categories.html')).render(context)
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
