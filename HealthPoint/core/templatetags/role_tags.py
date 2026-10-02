# core/templatetags/role_tags.py
from django import template

register = template.Library()

@register.filter
def has_group(user, group_name):
    """Uso: {% if request.user|has_group:'Supervisor' %} ... {% endif %}"""
    return user.is_authenticated and user.groups.filter(name=group_name).exists()
