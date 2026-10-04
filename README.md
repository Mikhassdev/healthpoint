# HealthPoint: Control de insumos médicos

![HealthPoint](HealthPoint/core/static/img/Portada.png)

Aplicación web en **Django** para controlar el inventario de insumos médicos de un centro de salud: registra insumos y boxes de atención, controla entradas y salidas de stock y alerta cuando un insumo llega a nivel crítico. El acceso está restringido por roles.

Proyecto final de la carrera **Analista Programador** (INACAP, 2025).

## Versiones

| Versión | Descripción |
|---|---|
| [`v1.0-evaluado`](../../tree/v1.0-evaluado) | El proyecto **tal como fue evaluado**. |
| [`v1.1`](../../tree/v1.1) | Corrección de errores, validaciones en el servidor, 19 pruebas automáticas y mejoras de uso. Detalle en [CHANGELOG.md](CHANGELOG.md). |

Cada corrección está en su propio *commit*, así que el historial muestra qué se cambió y por qué. El [mapa conceptual de cambios](docs/MAPA.md) los agrupa por tema.

## Funcionalidades

### Roles y permisos

| Rol | Página de inicio | Permisos |
|---|---|---|
| **Administrador** | Registro de usuarios | Crea usuarios y les asigna un rol |
| **Supervisor** | Panel de registro | Gestión completa, incluida la eliminación de insumos |
| **Bodega** | Panel de registro | Registra insumos, boxes y movimientos |
| **Enfermero** | Tablero | Solo lectura del tablero |

Cada usuario es redirigido automáticamente a su página según su rol, y las vistas están protegidas en el servidor con decoradores de permisos.

### Inventario

- **Insumos:** nombre, unidad de medida y stock inicial. El **stock mínimo se calcula automáticamente** como el 20 % del stock inicial.
- **Boxes:** nombre y responsable.
- **Movimientos de entrada y salida**, con nota opcional y registro del usuario que los realizó.
- **Reglas de negocio:**
  - No se permite una salida mayor al stock disponible.
  - Alerta visual cuando un insumo queda en stock crítico.

### Tablero

- Stock actual por insumo, calculado como `stock inicial + entradas − salidas`, con estado **OK** o **Crítico**.
- Listado de boxes.
- Últimos 20 movimientos, con fecha, tipo, insumo, box, cantidad, nota y usuario.

## Tecnologías

- Python 3.13
- Django 5.2
- SQLite
- HTML, CSS y JavaScript

## Estructura

```
├── Pipfile                     ← dependencias
└── HealthPoint/
    ├── manage.py
    ├── HealthPoint/            ← configuración del proyecto
    └── core/                   ← aplicación principal
        ├── models.py           ← Insumo, Box, Movimiento
        ├── views.py            ← vistas y control de permisos por rol
        ├── forms.py            ← formulario de creación de usuarios
        ├── tests.py            ← pruebas automáticas
        ├── management/         ← comando cargar_demo
        ├── templatetags/       ← filtro has_group para las plantillas
        ├── templates/          ← login, panel, tablero y registro de usuarios
        └── static/             ← estilos, JavaScript e imágenes
```

## Ejecutar en local

Requisitos: Python 3.13 y [pipenv](https://pipenv.pypa.io/).

```bash
git clone https://github.com/Mikhassdev/healthpoint.git
cd healthpoint
pipenv install
pipenv shell
cd HealthPoint
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Abre [http://localhost:8000/login/](http://localhost:8000/login/) e inicia sesión con el superusuario. Entrarás como Administrador y podrás crear usuarios para cada rol.

La base de datos no se incluye en el repositorio; `migrate` crea una vacía.

### Datos de demostración

Para probar la aplicación sin cargar datos a mano:

```bash
python manage.py cargar_demo
```

Crea un usuario por rol (`admin_demo`, `supervisor_demo`, `bodega_demo`, `enfermero_demo`, todos con la clave `demo-healthpoint`), además de insumos, boxes y movimientos de ejemplo. Estas cuentas son solo para uso local.

### Pruebas automáticas

```bash
python manage.py test core
```

Las pruebas cubren permisos por rol, redirección del login, reglas de stock, validación de movimientos y eliminación de insumos.

> Para un entorno distinto al local, define las variables de entorno `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False` y `DJANGO_ALLOWED_HOSTS` (dominios separados por coma).

## Autoría

- **Miguel Jorquera Marín**: autor.
- **JC-P**: colaborador.
