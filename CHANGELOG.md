# Historial de cambios

## v1.1 — 2026-10-03

Revisión del proyecto evaluado. Cada punto corresponde a un *commit* con su prueba automática cuando aplica.

### Errores corregidos

- **Eliminar por GET:** visitar `/insumos/<id>/eliminar/` borraba el insumo. Ahora solo se acepta POST.
- **Error 500 al eliminar:** un insumo con movimientos hacía caer la aplicación (`RestrictedError`). Ahora se informa al usuario y se conserva el historial.
- **Cantidad sin validar:** una cantidad negativa provocaba un error 500 y una cantidad 0 se guardaba. El servidor ahora exige una cantidad mayor a 0.
- **Tipo de movimiento sin validar:** se guardaba cualquier texto como tipo. Ahora solo se aceptan ENTRADA y SALIDA.
- **Usuario sin rol:** quedaba con la sesión iniciada aunque se le mostrara un error. Ahora no se inicia sesión.
- **Superusuario sin acciones visibles:** las vistas le daban acceso, pero las plantillas no le mostraban menús ni el botón Eliminar.
- **Indicador de movimientos:** el tablero nunca mostraba más de 20. Ahora muestra el total.
- **Login bloqueado en el navegador:** se exigía un usuario solo con letras y una clave con mayúscula, número y símbolo, reglas que Django no impone. Usuarios válidos no podían entrar.
- **Nombres rechazados:** la validación en el navegador no aceptaba números ni signos, por lo que rechazaba "Jeringa 5 ml" o "Dra. Pérez".
- **Campo de nota ausente:** el formulario de movimientos no tenía el campo, aunque el tablero mostraba la columna.
- **Avisos del tablero:** el tablero no mostraba los mensajes de éxito o error.

### Rendimiento

- Se eliminan consultas N+1 en el tablero (`select_related` y permiso calculado una sola vez).

### Configuración y mantenimiento

- `DEBUG` y `ALLOWED_HOSTS` se leen de variables de entorno.
- Idioma `es-cl` y zona horaria `America/Santiago`.
- Dependencias depuradas: se quitan paquetes sin uso y se fija Django a la serie 5.2.
- Se elimina código muerto (`RoleBasedLoginView`) e imports sin uso.
- Insumos, boxes y movimientos disponibles en el panel de administración.

### Experiencia de uso

- Insumo y box se eligen desde listas desplegables.
- Confirmación antes de eliminar un insumo.
- El botón "Index" pasa a llamarse "Panel de registro".

### Nuevo

- 19 pruebas automáticas (`python manage.py test core`).
- Comando `cargar_demo` con usuarios y datos de ejemplo.

## v1.0-evaluado

Versión entregada y evaluada como proyecto de título de Analista Programador (INACAP, 2025).
