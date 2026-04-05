# EasierDataBases

EasierDataBases es una plataforma no-code construida con Django para crear, administrar y operar bases de datos simples desde una interfaz visual, sin requerir conocimientos tecnicos.

La propuesta del producto hoy es clara: permitir que una persona o equipo organice informacion cotidiana sin caer en planillas desordenadas ni en sistemas demasiado complejos.

## Estado actual

La version actual esta orientada a:

- demos comerciales,
- pilotos cerrados,
- validacion con usuarios reales,
- y un modelo SaaS simple en etapa MVP avanzada.

No es todavia una version enterprise ni un lanzamiento publico masivo.

## Que ofrece hoy

### Creacion de bases

- Asistente de creacion por pasos.
- Plantillas iniciales:
  - Productos / Inventario
  - Alumnos / Cursos
  - Clientes / Contactos
  - Otra base
  - Desde cero
- Seleccion de campos base y extras durante la creacion.
- Posibilidad de agregar campos propios antes de confirmar.
- Datos demo opcionales.

### Modelado visual

- Campos personalizados.
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
- Columna principal del registro configurable.
- Reordenamiento visual de campos.
- Duplicado de campos.
- Edicion visual de estructura.
- Reglas de seguridad para impedir cambios destructivos cuando ya hay datos.

### Operacion diaria

- Vista principal en `Registros`.
- Tabla y tarjetas.
- Busqueda unificada por ID, nombre o contenido.
- Orden por columnas.
- Filtros avanzados por tipo de campo.
- Menu `...` por registro con:
  - editar
  - duplicar
  - archivar
  - eliminar definitivamente
- Duplicado de registros.
- Restauracion de scroll al operar dentro de la base.

### Relaciones entre bases

- Relaciones entre bases visibles para el usuario.
- Busqueda/autocomplete en campos de relacion por ID o texto.
- Creacion inline de un registro relacionado sin salir del formulario actual.
- Navegacion bidireccional entre registros relacionados.
- Tarjetas contextuales para previsualizar relaciones desde la tabla.

### CSV

- Importacion CSV guiada en 2 pasos:
  - subir archivo
  - revisar y mapear columnas
- Vista previa antes de importar.
- Procesamiento completo del archivo.
- Resumen de filas importadas y omitidas.
- Exportacion CSV por base.

### Estadisticas

- Pestana `Estadisticas` integrada dentro de cada base.
- Resumen automatico.
- Estadisticas utiles para operar.
- Constructor de analisis.
- Tipos de visualizacion:
  - barras
  - torta
  - tabla
  - metricas
- Interpretacion automatica.
- Comparacion basica entre periodos.
- Estadisticas guardadas.
- Vista ampliada del grafico.

### Historial y trazabilidad

- Pestana `Historial` por base.
- Registro de movimientos con:
  - accion
  - detalle
  - usuario
  - fecha
- Detalle enriquecido por movimiento.
- Comparacion `antes / ahora` en cambios de registros.

### Gestion y colaboracion

- Roles por base:
  - administrador
  - editor
- Cambio de nombre de base.
- Eliminacion segura de base.
- Gestion de registros archivados desde `Gestion`:
  - restaurar
  - eliminar definitivamente
  - restaurar todos
  - eliminar todos

### UI

- Landing comercial.
- Dashboard centrado en `Tus bases`.
- Dark mode con persistencia.
- Modo claro con paleta propia.
- Navbar fija.

## Organizacion de cada base

Cada base se organiza hoy en estas pestanas:

- `Registros`
- `Trabajo diario`
- `Estadisticas`
- `Estructura`
- `Gestion`
- `Historial`

## Stack tecnico

- Python 3.14
- Django 6
- SQLite en desarrollo
- PostgreSQL soportado via `DATABASE_URL`
- Templates server-rendered de Django
- CSS propio
- JavaScript liviano embebido en templates

Dependencias principales:

- `Django`
- `dj-database-url`
- `psycopg[binary]`

## Modelos principales

- `AppDatabase`
- `DatabaseMembership`
- `CustomField`
- `Record`
- `DatabaseActivity`
- `SavedStatistic`

## Seguridad e integridad ya resueltas

- `CustomField.key` estable despues de creado.
- Bloqueo de cambios de tipo inseguros con datos existentes.
- Bloqueo de cambio de base relacionada si el campo ya tiene datos.
- Bloqueo de eliminacion de campos con datos cargados.
- Relaciones filtradas por acceso permitido.
- Validacion backend de relaciones no autorizadas.
- Importacion CSV endurecida.
- Settings preparados por entorno.
- Logging basico.
- Paginas de error.

## Instalacion local

### 1. Crear entorno virtual

```powershell
python -m venv .venv
```

### 2. Activarlo

```powershell
.\.venv\Scripts\Activate.ps1
```

Si PowerShell bloquea la activacion:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### 3. Instalar dependencias

```powershell
pip install -r requirements.txt
```

### 4. Migrar

```powershell
python manage.py migrate
```

### 5. Levantar el servidor

```powershell
python manage.py runserver
```

Abrir:

- `http://localhost:8000/`

## Variables de entorno

Ver:

- `.env.example`

Variables importantes:

- `DJANGO_DEBUG`
- `DJANGO_SECRET_KEY`
- `DJANGO_ALLOWED_HOSTS`
- `DATABASE_URL`
- `DJANGO_SECURE_SSL_REDIRECT`

## Comandos utiles

```powershell
.\.venv\Scripts\python manage.py runserver
.\.venv\Scripts\python manage.py migrate
.\.venv\Scripts\python manage.py test
.\.venv\Scripts\python manage.py check
```

## Documentacion incluida

- `GUIA_DE_USO.md`: guia paso a paso para usuario final.
- `MANUAL_TECNICO.md`: explicacion tecnica completa del sistema.
- `PROXIMAS_ACTUALIZACIONES.md`: roadmap actualizado.

## Alcance real del MVP

Hoy el producto ya resuelve de verdad:

- creacion guiada de bases,
- modelado flexible,
- operacion diaria de registros,
- relaciones entre bases,
- importacion/exportacion,
- estadisticas iniciales,
- historial,
- y colaboracion basica.

Lo que todavia no apunta a cubrir:

- automatizaciones avanzadas,
- dashboards complejos,
- permisos finos,
- multi-tenant completo con workspaces,
- ni reporting avanzado tipo BI.
