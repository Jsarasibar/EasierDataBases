# EasierDataBases

EasierDataBases es una plataforma no-code construida con Django para crear, administrar y operar bases de datos simples desde una interfaz visual, sin requerir conocimientos tecnicos.

El producto esta pensado para negocios y equipos que hoy resuelven su operacion con planillas desordenadas o con herramientas demasiado complejas para sus necesidades diarias. La propuesta actual del MVP es ofrecer una experiencia clara para crear bases operativas, definir campos personalizados, cargar registros, relacionar informacion y trabajar sobre esos datos con filtros, importacion/exportacion, estadisticas y colaboracion basica.

## Estado del proyecto

La version actual apunta a:

- demos comerciales,
- pilotos cerrados con usuarios reales,
- validacion de producto en un modelo SaaS simple.

No esta pensada todavia como version final de lanzamiento publico masivo.

## Que resuelve

EasierDataBases busca ubicarse entre dos extremos:

- una planilla flexible pero desordenada,
- y un sistema mas robusto pero dificil de aprender.

La idea es que cualquier persona pueda crear su propia base para gestionar informacion cotidiana sin programar.

Casos de uso que hoy encajan bien:

- inventario y catalogos,
- alumnos y cursos,
- clientes y contactos,
- pedidos y seguimientos simples,
- tareas operativas,
- listas internas personalizadas.

## Funcionalidades actuales

### Acceso y cuentas

- Registro de usuarios.
- Inicio y cierre de sesion.
- Recuperacion de contrasena.

### Creacion guiada de bases

- Asistente de creacion por pasos.
- Plantillas iniciales:
  - Productos / Inventario
  - Alumnos / Cursos
  - Clientes / Contactos
  - Otra base
  - Desde cero
- Seleccion de campos base y extras desde el asistente.
- Posibilidad de agregar campos propios antes de crear la base.
- Datos demo opcionales.

### Modelado visual de la base

- Campos personalizados sin codigo.
- Tipos de campo:
  - texto
  - numero
  - moneda
  - si / no
  - fecha
  - email
  - telefono
  - seleccion
  - relacion con otra base
- Editor visual de estructura.
- Reordenamiento visual de campos.
- Duplicado de campos.
- Vista previa del formulario.
- Selector visible para definir que columna identifica el nombre del registro.
- Reglas de seguridad para evitar cambios destructivos.

### Operacion de registros

- Crear, editar, duplicar y eliminar registros.
- Campo principal del registro configurable por base.
- Prioridad opcional por base (`normal`, `high`, `urgent`).
- Vista de tabla y vista de tarjetas.
- Busqueda, filtros, orden por columnas, filtro por ID y paginacion.
- Filtros avanzados segun el tipo de campo.
- Menu `...` por registro con acciones rapidas.
- Cambio rapido de prioridad desde el menu contextual.
- Vista operativa centrada en `Registros`.
- Pestana `Trabajo diario`.
- Dark mode global con persistencia entre paginas.

### Relaciones entre bases

- Campos de relacion hacia otra base.
- Navegacion bidireccional entre registros relacionados.
- Restriccion de relaciones segun acceso autorizado.
- Tarjeta contextual al hacer clic sobre un valor relacionado en la tabla.
- Posibilidad de crear un registro relacionado sin salir del formulario actual.
- Busqueda en campos de relacion por ID o texto.

### Importacion y exportacion

- Importacion CSV guiada por mapeo.
- Vista previa antes de confirmar.
- Conteo total de filas detectadas.
- Procesamiento del archivo completo.
- Resumen de filas importadas y omitidas.
- Exportacion CSV por base.

### Roles y acceso

- Roles basicos por base:
  - administrador
  - editor
- Aislamiento por membresia.
- Restriccion de relaciones y registros segun acceso visible.
- Eliminacion segura de bases con confirmacion explicita.

### Estadisticas

- Pestana `Estadisticas` dentro de cada base.
- Resumen automatico.
- Estadisticas utiles para operar.
- Analisis por campo con visualizaciones adaptadas al tipo de dato.
- Tipos de vista:
  - barras
  - torta
  - tabla
  - metricas
- Interpretacion automatica del resultado.
- Comparacion basica entre periodos.
- Estadisticas guardadas por base.
- Vista ampliada del grafico.

### Historial y trazabilidad

- Pestana `Historial` por base.
- Registro de movimientos con accion, usuario y fecha.
- Tarjeta de detalle por movimiento.
- Comparacion `antes / ahora` en cambios de registros.

## Vistas del producto

Cada base esta organizada en pestanas para reducir complejidad:

- `Registros`
- `Trabajo diario`
- `Estadisticas`
- `Estructura`
- `Gestion`
- `Historial`

## Stack tecnologico

- Python 3.14
- Django 6
- SQLite en desarrollo
- PostgreSQL en produccion via `DATABASE_URL`
- HTML con templates de Django
- CSS propio

Dependencias principales:

- `Django`
- `dj-database-url`
- `psycopg[binary]`

## Arquitectura general

- `config/`: configuracion principal del proyecto.
- `app/`: dominio principal, modelos, formularios, vistas y rutas.
- `templates/`: interfaz renderizada del lado servidor.
- `static/`: estilos y assets.

Entidades principales:

- `AppDatabase`: representa una base creada por el usuario.
- `DatabaseMembership`: define acceso y rol sobre cada base.
- `CustomField`: modela los campos configurables.
- `Record`: representa cada registro cargado.
- `DatabaseActivity`: historial por base.
- `SavedStatistic`: configuraciones guardadas del modulo de estadisticas.

## Seguridad y hardening ya implementado

- `CustomField.key` estable despues de la creacion.
- Bloqueo de cambios de tipo cuando un campo ya contiene datos.
- Bloqueo de cambio de base relacionada si el campo ya tiene datos.
- Bloqueo de eliminacion de campos con datos cargados.
- Filtro de relaciones por bases accesibles al usuario.
- Validacion backend para impedir referencias no autorizadas.
- Importacion CSV segura frente a duplicados en relaciones.
- Settings preparados por variables de entorno.
- Cookies seguras y redireccion SSL configurables.
- Logging basico para errores operativos.
- Paginas 404 y 500.
- `manage.py check --deploy` sin issues en la configuracion actual.

## Instalacion local

### 1. Crear el entorno virtual

```powershell
python -m venv .venv
```

### 2. Activarlo

```powershell
.\.venv\Scripts\Activate.ps1
```

Si PowerShell bloquea la activacion por politica de ejecucion:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### 3. Instalar dependencias

```powershell
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Ejemplo recomendado para desarrollo:

```env
DJANGO_SECRET_KEY=replace-with-a-long-random-secret
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,testserver
DATABASE_URL=sqlite:///db.sqlite3
DJANGO_DEFAULT_FROM_EMAIL=no-reply@easierdatabases.local
DJANGO_EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### 5. Aplicar migraciones

```powershell
python manage.py migrate
```

### 6. Ejecutar el servidor

```powershell
python manage.py runserver
```

La app quedara disponible en:

- [http://localhost:8000](http://localhost:8000)
- [http://127.0.0.1:8000](http://127.0.0.1:8000)

## Acceso por red local

```powershell
python manage.py runserver 0.0.0.0:8000
```

Luego abrir desde otro dispositivo:

```text
http://TU_IP_LOCAL:8000
```

## Comandos utiles

```powershell
python manage.py test
python manage.py check
python manage.py check --deploy
python manage.py createsuperuser
python manage.py collectstatic
```

## Flujo principal del usuario

1. El usuario se registra o inicia sesion.
2. Crea una nueva base con el asistente.
3. Elige una plantilla o arranca desde cero.
4. Selecciona los campos iniciales y agrega propios si hace falta.
5. Empieza a operar registros desde `Registros`.
6. Si necesita, usa `Trabajo diario`, analiza datos en `Estadisticas`, edita la estructura, agrega relaciones, importa CSV o comparte acceso.

## Experiencia actual del producto

- El dashboard destaca `Tus bases` como bloque principal de trabajo.
- Al entrar a una base, la vista inicial es `Registros`.
- `Registros` concentra tabla, filtros avanzados, orden por columnas y acciones por registro.
- `Trabajo diario` concentra lo importante del dia.
- `Estadisticas` muestra resumen, lectura operativa, analisis por campo e interpretacion.
- `Estructura` concentra configuracion de campos, relaciones, duplicado y orden visual.
- `Gestion` reune importacion/exportacion, permisos y acciones sensibles.
- `Historial` concentra trazabilidad y detalle de movimientos.

## Cobertura actual de tests

La suite automatizada cubre flujos centrales del MVP, incluyendo:

- creacion de bases con wizard,
- persistencia del wizard entre pasos,
- creacion, edicion y duplicado de registros,
- cambio de columna principal del registro,
- plantillas iniciales,
- importacion y exportacion CSV,
- importaciones de mas de 50 filas,
- relaciones entre bases,
- relaciones bidireccionales,
- creacion inline de registros relacionados,
- busqueda de relaciones por ID y texto,
- filtros avanzados y orden de registros,
- reordenamiento y duplicado de campos,
- historial de movimientos,
- detalle de cambios antes / despues en edicion de registros,
- restricciones de acceso en relaciones,
- renombre seguro de campos,
- bloqueo de cambios destructivos,
- eliminacion protegida de bases.

## Limitaciones actuales

El producto todavia no incluye:

- automatizaciones complejas,
- dashboards avanzados multiwidget,
- reportes ejecutivos exportables,
- formularios publicos,
- billing,
- auditoria detallada por registro a nivel fino,
- permisos por campo o por accion fina,
- organizaciones/workspaces de nivel enterprise.

## Roadmap recomendado

Siguientes pasos naturales:

1. profundizar filtros y microacciones de uso diario,
2. madurar el modulo de estadisticas y comparacion,
3. sumar permisos y colaboracion mas finos,
4. introducir `workspace` u `organization` como frontera SaaS explicita,
5. incorporar automatizaciones simples,
6. avanzar hacia onboarding asistido mas inteligente.
