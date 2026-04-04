# EasierDataBases

EasierDataBases es una plataforma no-code construida con Django para crear, administrar y operar bases de datos simples desde una interfaz visual, sin requerir conocimientos tecnicos.

El producto esta pensado para negocios y equipos que hoy resuelven su operacion con planillas desordenadas o con herramientas demasiado complejas para sus necesidades diarias. La propuesta actual del MVP es ofrecer una experiencia clara para crear bases operativas, definir campos personalizados, cargar registros, relacionar informacion y trabajar sobre esos datos con filtros, importacion/exportacion y colaboracion basica.

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
- Vista previa del formulario.
- Selector visible para definir que columna identifica el nombre del registro.
- Reglas de seguridad para evitar cambios destructivos.

### Operacion de registros

- Crear, editar y eliminar registros.
- Campo principal del registro configurable por base.
- Prioridad opcional por base (`normal`, `high`, `urgent`).
- Vista de tabla y vista de tarjetas.
- Busqueda, filtros, orden, filtro por ID y paginacion.
- Vista operativa centrada en `Registros`.
- Pestaña `Trabajo diario`.
- Dark mode global con persistencia entre paginas.

### Relaciones entre bases

- Campos de relacion hacia otra base.
- Navegacion bidireccional entre registros relacionados.
- Restriccion de relaciones segun acceso autorizado.
- Tarjeta contextual al hacer clic sobre un valor relacionado en la tabla.
- Posibilidad de crear un registro relacionado sin salir del formulario actual.

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

### Historial y trazabilidad

- Pestaña `Historial` por base.
- Registro de movimientos con accion, usuario y fecha.
- Tarjeta de detalle por movimiento.
- Comparacion `antes / ahora` en cambios de registros.

### Vistas del producto

Cada base esta organizada en pestañas para reducir complejidad:

- `Registros`
- `Trabajo diario`
- `Resumen`
- `Estructura`
- `Gestion`
- `Historial`

Ademas existe una vista separada de `Estadisticas`, actualmente marcada como `Coming soon`.

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
- `SavedView`: modelo heredado del MVP inicial, no expuesto actualmente en la interfaz principal.

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
- El servidor local debe abrirse con `http://localhost:8000/` o `http://127.0.0.1:8000/`.

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

- [http://localhost:8000](http://localhost:8000)
- [http://127.0.0.1:8000](http://127.0.0.1:8000)

Si tu navegador intenta forzar HTTPS en local, prueba con `http://localhost:8000/` en una ventana privada.

## Acceso por red local

Para probar la app desde otros dispositivos de la misma red:

1. Levanta el servidor escuchando en toda la red local:

```powershell
python manage.py runserver 0.0.0.0:8000
```

2. Averigua la IP IPv4 de tu equipo:

```powershell
ipconfig
```

3. Abre desde otro dispositivo:

```text
http://TU_IP_LOCAL:8000
```

Si no responde, revisa el firewall de Windows y permite el puerto `8000`.

## Comandos utiles

Ejecutar tests:

```powershell
python manage.py test
```

Chequeo general:

```powershell
python manage.py check
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
4. Selecciona los campos iniciales y agrega propios si hace falta.
5. Empieza a operar registros desde `Registros`.
6. Si necesita, usa `Trabajo diario`, edita la estructura, agrega relaciones, importa CSV o comparte acceso.

## Experiencia actual del producto

- El dashboard destaca `Tus bases` como bloque principal de trabajo, junto con accesos rapidos, ideas de arranque y actividad reciente.
- Al entrar a una base, la vista inicial es `Registros`.
- `Trabajo diario` concentra lo importante del dia.
- `Resumen` muestra estado general y acceso a `Estadisticas`.
- `Estructura` concentra configuracion de campos, relaciones y columna principal del registro.
- `Gestion` reune importacion/exportacion y permisos.
- `Historial` concentra trazabilidad y detalle de movimientos.

## Cobertura actual de tests

La suite automatizada cubre flujos centrales del MVP, incluyendo:

- creacion de bases con wizard,
- persistencia del wizard entre pasos,
- creacion y edicion de registros,
- cambio de columna principal del registro,
- plantillas iniciales,
- importacion y exportacion CSV,
- importaciones de mas de 50 filas,
- relaciones entre bases,
- relaciones bidireccionales,
- creacion inline de registros relacionados,
- historial de movimientos,
- detalle de cambios antes / despues en edicion de registros,
- restricciones de acceso en relaciones,
- renombre seguro de campos,
- bloqueo de cambios destructivos,
- eliminacion protegida de bases.

## Criterios de calidad ya validados

Actualmente el proyecto pasa:

- `python manage.py test`
- `python manage.py check`
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
- organizaciones/workspaces de nivel enterprise,
- estadisticas funcionales dentro de la vista `Estadisticas` (por ahora es una pantalla informativa).

## Roadmap recomendado

Siguientes pasos naturales:

1. Introducir `workspace` u `organization` como frontera SaaS explicita.
2. Agregar auditoria e historial de cambios.
3. Mejorar importacion con reporte descargable de errores.
4. Sumar estadisticas reales por campos.
5. Incorporar automatizaciones simples.
6. Avanzar hacia onboarding asistido mas inteligente.
