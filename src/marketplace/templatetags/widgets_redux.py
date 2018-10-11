import copy

from django import template


register = template.Library()


@register.simple_tag
def render_widget(target, **kwargs):
    """Render the given widget with modified data.

    Keys may refer to nested dictionaries with double-underscores:

        render_widget org_button label="Do it!" attrs__class="btn text-white"

    """
    widget = copy.deepcopy(target)

    data = widget.data
    for (key, value) in kwargs.items():
        key_data = data
        (*key_parts, key_leaf) = key.split('__')
        for part in key_parts:
            key_data = key_data.setdefault(part, {})
        key_data[key_leaf] = value

    return widget


@register.simple_tag(takes_context=True)
def select(context, name, iterable, **kwargs):
    """Select the first matching item from the given sequence and set a
    given reference to this item.

    """
    for item in iterable:
        for (key, value) in kwargs.items():
            try:
                if getattr(item, key) != value:
                    # give up on this item
                    break
            except AttributeError:
                # give up on this item
                break
        else:
            # item passed all tests
            # give up on remainder
            break
    else:
        # no items passed tests or no items
        item = None

    context[name] = item
    return ''
