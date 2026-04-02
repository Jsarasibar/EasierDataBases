from django import template


register = template.Library()


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, "")


@register.filter
def display_value(record, field):
    return record.get_display_value(field)
