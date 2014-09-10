from django import template


register = template.Library()


@register.tag
def sitecats_categories(parser, token):
    return get_generic_node(parser, token,
           '`sitecats_categories` tag expects the following notation: {% sitecats_categories from my_categories_list template "sitecats/my_categories.html" %}.',
           'sitecats_categories', 'sitecats/categories.html')


def get_generic_node(parser, token, error_msg, context_var, default_template):
    """Returns a generic node object for a template tag.

    :param Parser parser:
    :param Token token:
    :param str error_msg:
    :param str context_var:
    :param str default_template:
    :return:
    """
    tokens = token.split_contents()
    use_template = detect_clause(parser, 'template', tokens)
    target_obj = detect_clause(parser, 'from', tokens)

    tokens_num = len(tokens)

    if tokens_num in (1, 3):
        return sitecats_genericNode(target_obj, use_template, context_var, default_template)
    else:
        raise template.TemplateSyntaxError(error_msg)


class sitecats_genericNode(template.Node):

    def __init__(self, target_obj, use_template, context_var, default_template):
        self.use_template = use_template
        self.target_obj = target_obj
        self.context_var = context_var
        self.default_template = default_template

    def render(self, context):
        resolve = lambda arg: arg.resolve(context) if isinstance(arg, template.FilterExpression) else arg

        context.push()
        target_obj = resolve(self.target_obj)
        if not isinstance(target_obj, (list, tuple)):
            target_obj = (target_obj,)
        context[self.context_var] = target_obj
        contents = template.loader.get_template(resolve(self.use_template or self.default_template)).render(context)
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
