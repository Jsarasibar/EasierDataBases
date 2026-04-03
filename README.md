# EasierDataBases

EasierDataBases es una plataforma no-code construida con Django para crear, administrar y operar bases de datos simples desde una interfaz visual, sin requerir conocimientos tecnicos.

El producto esta pensado para negocios y equipos que hoy resuelven su operacion con planillas desordenadas o con herramientas demasiado complejas para sus necesidades diarias. La propuesta del MVP es ofrecer una experiencia clara para crear listas operativas, definir campos personalizados, cargar registros, relacionar informacion y trabajar sobre esos datos con filtros, vistas y herramientas basicas de colaboracion.

## Estado del proyecto

La version actual apunta a:

- demos comerciales,
- pilotos cerrados con usuarios reales,
- validacion de producto en modelo SaaS simple.

No esta pensada todavia como version final de lanzamiento publico masivo.

## Propuesta del MVP

El MVP permite crear bases de uso general con un enfoque no-code, usando productos como caso de arranque pero sin limitarse a un solo nicho.

Casos de uso que hoy encajan bien:

- inventario y catalogos,
- alumnos y cursos,
- clientes y contactos,
- tareas operativas,
- pedidos y seguimientos simples,
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
- Extras sugeridos por plantilla.
- Datos demo opcionales.
- Modo inicial simple o avanzado.

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
- Vista previa del formulario.
- Reglas de seguridad para evitar cambios destructivos.

### Operacion de registros

- Crear, editar y eliminar registros.
- Prioridades (`normal`, `high`, `urgent`).
- Vista de tabla y vista de tarjetas.
- Busqueda, filtros, orden y paginacion.
- Vistas guardadas por usuario.
- Pestaña de trabajo diario.

### Relaciones entre bases

- Campos de relacion hacia otra base.
- Navegacion bidireccional entre registros relacionados.
- Restriccion de relaciones segun acceso autorizado.

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

- `AppDatabase`: representa una base o lista creada por el usuario.
- `DatabaseMembership`: define acceso y rol sobre cada base.
- `CustomField`: modela los campos configurables.
- `Record`: representa cada registro cargado.
- `SavedView`: guarda filtros y modos de vista por usuario.

## Seguridad y hardening ya implementado

- `CustomField.key` estable despues de la creacion.
- Bloqueo de cambios de tipo cuando un campo ya contiene datos.
- Bloqueo de eliminacion de campos con datos cargados.
- Filtro de relaciones por bases accesibles al usuario.
- Validacion backend para impedir referencias no autorizadas.
- Settings preparados por variables de entorno.
- Cookies seguras y redireccion SSL configurables.
- Logging basico para errores operativos.
- Paginas 404 y 500.
- `manage.py check --deploy` sin issues en la configuracion actual.

## Requisitos

- Python 3.14 o compatible
- `pip`
- Virtualenv recomendado

Para produccion:

- PostgreSQL 14+

## Instalacion local

### 1. Crear el entorno virtual

```powershell
python -m venv .venv
```

### 2. Activarlo

```powershell
.\.venv\Scripts\Activate.ps1
```

Si PowerShell bloquea la activacion por politica de ejecucion, puedes habilitar scripts para tu usuario:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Y luego volver a ejecutar:

```powershell
.\.venv\Scripts\Activate.ps1
```

Si prefieres no activar el entorno, puedes usar directamente el ejecutable del entorno virtual:

```powershell
.\.venv\Scripts\python manage.py runserver
```

### 3. Instalar dependencias

```powershell
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Puedes usar `.env.example` como referencia. El proyecto lee automaticamente un archivo `.env` en la raiz si existe.

Configuracion recomendada para desarrollo local:

```env
DJANGO_SECRET_KEY=replace-with-a-long-random-secret
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,testserver
DATABASE_URL=sqlite:///db.sqlite3
DJANGO_DEFAULT_FROM_EMAIL=no-reply@easierdatabases.local
DJANGO_EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

Notas importantes:

- Para desarrollo normal, `DJANGO_DEBUG=True` es lo recomendado.
- Con `python manage.py runserver`, EasierDataBases desactiva automaticamente la redireccion SSL local.
- El servidor local debe abrirse con `http://127.0.0.1:8000/`.

Ejemplo para PostgreSQL:

```env
DATABASE_URL=postgresql://usuario:clave@localhost:5432/easierdatabases
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

- [http://127.0.0.1:8000](http://127.0.0.1:8000)

Si el navegador intenta abrir `https://127.0.0.1:8000/`, escribe manualmente `http://127.0.0.1:8000/` o prueba en una ventana privada.

## Comandos utiles

Ejecutar tests:

```powershell
python manage.py test
```

Chequeo de deploy:

```powershell
python manage.py check --deploy
```

Crear superusuario:

```powershell
python manage.py createsuperuser
```

Recolectar archivos estaticos:

```powershell
python manage.py collectstatic
```

## Configuracion de entorno

### Desarrollo

- `DJANGO_DEBUG=True`
- `DATABASE_URL=sqlite:///db.sqlite3`
- backend de email por consola
- `runserver` funciona por HTTP local sin redireccion forzada a HTTPS

### Produccion

Recomendaciones minimas:

- `DJANGO_DEBUG=False`
- `DATABASE_URL` apuntando a PostgreSQL
- `DJANGO_ALLOWED_HOSTS` definido explicitamente
- `DJANGO_SECRET_KEY` segura y privada
- backend de email real
- HTTPS terminado en proxy o balanceador

El proyecto ya contempla:

- `SECURE_SSL_REDIRECT`
- `SESSION_COOKIE_SECURE`
- `CSRF_COOKIE_SECURE`
- `SECURE_HSTS_SECONDS`
- `SECURE_HSTS_INCLUDE_SUBDOMAINS`
- `SECURE_HSTS_PRELOAD`
- `SECURE_PROXY_SSL_HEADER`

## Flujo principal del usuario

1. El usuario se registra o inicia sesion.
2. Crea una nueva base con el asistente.
3. Elige una plantilla o arranca desde cero.
4. Ajusta campos sugeridos y carga datos demo si quiere.
5. Empieza a operar registros desde la vista diaria o la pestaña de registros.
6. Si necesita, edita la estructura, agrega relaciones, importa CSV o comparte acceso.

## Experiencia de producto actual

La interfaz esta organizada en pestañas para reducir complejidad:

- `Resumen`
- `Trabajo diario`
- `Registros`
- `Estructura`
- `Gestion`

Esto permite separar:

- operacion cotidiana,
- configuracion de estructura,
- importacion/exportacion,
- administracion basica del equipo.

## Cobertura actual de tests

La suite automatizada cubre flujos centrales del MVP, incluyendo:

- creacion de bases con wizard,
- creacion y edicion de registros,
- plantillas iniciales,
- importacion y exportacion CSV,
- relaciones entre bases,
- relaciones bidireccionales,
- edicion de campos,
- renombre seguro de campos,
- importaciones de mas de 50 filas,
- restricciones de acceso en relaciones,
- bloqueo de borrado de campos con datos.

## Criterios de calidad ya validados

Actualmente el proyecto pasa:

- `python manage.py test`
- `python manage.py check --deploy`

## Limitaciones actuales

El producto todavia no incluye:

- automatizaciones complejas,
- dashboards avanzados,
- reportes ejecutivos,
- formularios publicos,
- billing,
- auditoria detallada de cambios,
- permisos por campo o por accion fina,
- organizaciones/workspaces de nivel enterprise.

## Roadmap recomendado

Siguientes pasos naturales:

1. Introducir `workspace` u `organization` como frontera SaaS explicita.
2. Agregar auditoria e historial de cambios.
3. Mejorar importacion con reporte descargable de errores.
4. Sumar relaciones mas ricas y vistas conectadas.
5. Incorporar automatizaciones simples.
6. Avanzar hacia onboarding asistido mas inteligente.
