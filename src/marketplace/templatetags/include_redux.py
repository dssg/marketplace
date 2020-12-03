from django import template
from django.template import loader_tags


register = template.Library()


class IncludeStrippedNode(loader_tags.IncludeNode):
    """IncludeNode which strips leading & trailing white space from
    its rendering.

    """
    def render(self, context):
        return super().render(context).strip()


@register.tag('include-stripped')
def do_include_stripped(parser, token):
    """Include template -- exactly as "include" -- but with leading &
    trailing white space stripped.

    Particularly useful for inclusion templates intended to render
    compact node attribute values (rather than markup).

    """
    include_node = loader_tags.do_include(parser, token)
    include_node.__class__ = IncludeStrippedNode
    return include_node
