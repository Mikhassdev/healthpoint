# core/templatetags/role_tags.py
from django import template

from core.views import user_in_groups

register = template.Library()

@register.filter
def has_group(user, group_name):
    """Uso: {% if request.user|has_group:'Supervisor' %} ... {% endif %}

    Usa la misma regla que las vistas (user_in_groups), así lo que se muestra
    coincide con lo que el servidor permite, incluido el superusuario.
    """
    return user_in_groups(user, [group_name])
