from django import template

register = template.Library()

@register.filter
def get_q_field(form, num):
    """Dynamically get the 'qN' field from the form, where N is the question number."""
    return form[f'q{num}']  # Use dictionary lookup instead of getattr