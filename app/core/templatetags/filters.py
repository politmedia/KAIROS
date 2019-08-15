from django import template

register = template.Library()

@register.filter()
def label_with_class(value, arg):
    return value.label_tag(attrs={'class': arg})


@register.filter()
def get_item(dictionary, key):
    return dictionary.get(key)