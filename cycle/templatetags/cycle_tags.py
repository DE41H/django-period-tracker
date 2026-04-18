from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def phase_color(phase_name):
    colors = {
        'menstrual': 'rose',
        'follicular': 'blue',
        'ovulation': 'purple',
        'luteal': 'amber',
    }
    return colors.get(phase_name, 'gray')


@register.filter
def sev_class(severity):
    return f'sev-{severity}'
