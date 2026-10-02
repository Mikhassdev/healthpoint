# core/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Group

ROLES_CHOICES = [
    ("Administrador", "Administrador"),
    ("Supervisor", "Supervisor"),
    ("Bodega", "Bodega"),
    ("Enfermero", "Enfermero"),
]

class UserCreateForm(UserCreationForm):
    first_name = forms.CharField(label="Nombre", max_length=30, required=False)
    last_name  = forms.CharField(label="Apellidos", max_length=150, required=False)
    email      = forms.EmailField(label="Correo electrónico", required=False)
    role       = forms.ChoiceField(label="Rol de usuario", choices=ROLES_CHOICES)

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "password1", "password2", "role"]

    def save(self, commit=True):
        user = super().save(commit=commit)
        role_name = self.cleaned_data.get("role")

        if commit and role_name:
            group, _ = Group.objects.get_or_create(name=role_name)
            user.groups.add(group)

        return user
