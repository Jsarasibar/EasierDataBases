# Manual tecnico de EasierDataBases

## 1. Objetivo

Este documento explica como funciona EasierDataBases a nivel tecnico y funcional.

Sirve para entender:

- arquitectura general,
- entidades del dominio,
- flujo interno del producto,
- organizacion de vistas y templates,
- y comportamiento actual de cada modulo.

## 2. Vision general

EasierDataBases es una plataforma no-code basada en Django para crear y operar bases de datos simples desde una interfaz visual.

La unidad central del sistema es `AppDatabase`: una base creada por un usuario, con sus campos, registros, miembros, estadisticas e historial.

## 3. Stack

- Python 3.14
- Django 6
- SQLite para desarrollo local
- PostgreSQL soportado por `DATABASE_URL`
- Templates server-rendered de Django
- CSS propio
- JavaScript liviano embebido en templates

## 4. Estructura del proyecto

- `config/`
  - settings, urls y configuracion global
- `app/`
  - modelos, formularios, vistas, urls y tests
- `templates/`
  - UI server-rendered
- `static/`
  - estilos y assets
- `tmp/`
  - uploads temporales, especialmente para importacion CSV

## 5. Modelos principales

### `AppDatabase`

Representa una base creada por el usuario.

Responsabilidades:

- nombre, slug y descripcion
- use case
- configuracion general
- relacion con campos, registros, miembros, historial y estadisticas guardadas

### `DatabaseMembership`

Relacion usuario-base.

Roles actuales:

- `admin`
- `editor`

Se usa para aislamiento funcional y permisos dentro de cada base.

### `CustomField`

Modela un campo configurable dentro de una base.

Campos relevantes:

- `label`
- `key`
- `field_type`
- `required`
- `show_in_table`
- `help_text`
- `is_primary`
- `options_text`
- `relation_database`
- `position`

Reglas clave:

- `key` se genera una sola vez y luego queda estable
- `position` define el orden visual
- si ya hay datos cargados, se restringen cambios destructivos
- si es un campo de relacion con datos, no se puede cambiar su base destino

### `Record`

Representa un registro dentro de una base.

Campos relevantes:

- `database`
- `title`
- `priority`
- `data`
- `created_by`
- `updated_by`
- `archived_at`
- `archived_by`

Notas:

- los datos variables viven en `JSONField`
- `title` se sincroniza con el campo principal de la base
- el archivado es logico, no fisico

### `DatabaseActivity`

Historial por base.

Guarda:

- accion
- detalle
- usuario
- fecha
- payload enriquecido

### `SavedStatistic`

Guarda configuraciones reutilizables de analisis por base.

## 6. Flujo general del producto

1. el usuario se registra o inicia sesion
2. entra al dashboard
3. crea una base o abre una existente
4. configura estructura
5. carga registros manualmente o por CSV
6. opera desde `Registros` o `Trabajo diario`
7. analiza en `Estadisticas`
8. gestiona miembros, importaciones y archivados desde `Gestion`
9. revisa trazabilidad en `Historial`

## 7. Dashboard

El dashboard actual esta organizado para priorizar `Tus bases`.

Secciones:

- `Tus bases`
- `Accesos rapidos`
- `Resumen rapido`
- `Ideas para empezar`
- `Actividad reciente`

## 8. Flujo de creacion de bases

La creacion se hace con un asistente de 4 pasos:

1. elegir plantilla
2. poner nombre
3. completar estructura inicial
4. confirmar

En el paso 3 se pueden:

- activar o desactivar campos base
- sumar extras
- activar prioridad
- agregar campos propios

Al confirmar se crean:

- la base
- los campos
- el campo principal si corresponde
- registros demo opcionales
- la membresia admin del creador
- actividad inicial en historial

## 9. Organizacion interna de una base

Cada base se estructura en estas pestanas:

- `Registros`
- `Trabajo diario`
- `Estadisticas`
- `Estructura`
- `Gestion`
- `Historial`

## 10. `Registros`

Es la vista principal de operacion.

### Capacidades actuales

- tabla y tarjetas
- busqueda unificada por ID, nombre o contenido
- orden por columnas
- filtros avanzados por tipo de campo
- paginacion
- menu `...` por registro

### Menu `...`

Acciones actuales:

- editar
- duplicar
- archivar
- eliminar definitivamente

`Eliminar` ya no usa `confirm()` del navegador: abre un modal propio de la aplicacion.

### Orden por columnas

Los encabezados son clickeables.

El sistema soporta orden para:

- `id`
- `title`
- `priority`
- y campos compatibles de `CustomField`

### Scroll restore

La app guarda y restaura `scrollY` al hacer submit o al ordenar en bases abiertas.

La logica vive en `templates/base.html`.

## 11. `Trabajo diario`

Es una vista mas reducida y operativa.

Busca concentrar:

- foco del dia
- acciones rapidas
- continuidad de trabajo

## 12. `Estadisticas`

### Estructura actual

1. resumen automatico
2. estadisticas utiles para operar
3. workspace principal:
   - constructor
   - resultado / grafico
   - interpretacion
4. comparacion
5. estadisticas guardadas

### Capacidades

- analisis por campo
- tipos de visualizacion por tipo de dato
- filtros avanzados
- comparacion basica entre periodos
- interpretacion textual
- vista ampliada del grafico

### Tipos de visualizacion

- barras
- torta
- tabla
- metricas

### Persistencia

Las estadisticas guardadas se almacenan en `SavedStatistic`.

## 13. `Estructura`

Editor visual de la base.

### Permite

- crear campos
- editar campos
- duplicar campos
- moverlos arriba y abajo
- definir relaciones
- marcar obligatoriedad
- controlar visibilidad en tabla
- configurar ayuda
- elegir el campo principal del registro

### Reordenamiento

Se resuelve con `position` en `CustomField` y acciones `field_move`.

El reordenamiento actual no recarga toda la pagina: se maneja con fetch + DOM update.

## 14. `Gestion`

Hoy esta ordenada asi:

1. `Datos y operaciones`
2. `Equipo y permisos`
3. `Archivados`
4. `Zona sensible`

### Importacion CSV

Flujo actual:

1. subir archivo
2. revisar y mapear columnas

Detalles:

- el archivo se guarda temporalmente
- se inspecciona para detectar encabezados y preview
- el mapeo se resuelve en una pantalla separada
- luego se procesa el archivo completo

### Archivados

Se gestionan desde `Gestion > Archivados`.

Permite:

- restaurar un registro archivado
- eliminarlo definitivamente
- restaurar todos
- eliminar todos

## 15. Relaciones entre bases

### Definicion

Se crean mediante `CustomField` de tipo `relation`.

### Restricciones

- solo se pueden relacionar bases visibles para el usuario
- se valida backend ante envios manipulados

### Uso en formularios

Los campos de relacion hoy soportan:

- busqueda/autocomplete por ID o texto
- alta inline de un registro relacionado

### Visualizacion

- navegacion bidireccional
- preview contextual de registros relacionados
- detalle del registro relacionado

## 16. CSV

### Importacion

Se apoya en:

- `CSVImportForm`
- `CSVMappingForm`
- vistas `records_import_start` y `records_import_map`

### Exportacion

Genera CSV server-side desde la base actual.

## 17. Archivado y borrado

### Archivado

`record_archive` marca:

- `archived_at`
- `archived_by`

El registro deja de aparecer en el queryset activo.

### Restauracion

`record_restore` limpia esos campos.

### Borrado definitivo

`record_delete` elimina el registro fisicamente.

Se usa:

- desde `Registros`
- y desde `Gestion > Archivados`

## 18. Historial

El historial registra movimientos como:

- creacion de bases
- cambios de estructura
- carga y edicion de registros
- importacion/exportacion
- restauracion y archivado
- eliminacion definitiva

Cuando corresponde, el payload guarda:

- resumen
- cambios `antes / ahora`
- detalles adicionales

## 19. Seguridad e integridad

### Ya implementado

- key estable en campos
- validacion de cambios inseguros
- validacion de relaciones
- bloqueo de eliminacion de campos con datos
- aislamiento por membresia
- configuracion por entorno
- soporte para hardening de produccion

## 20. Frontend y estilo

### Render

La UI es server-rendered con templates Django.

### CSS

La mayor parte vive en `static/styles/app.css`.

### JS

Se usa JS embebido y liviano para:

- modales
- expanders inline
- restauracion de scroll
- menus flotantes
- importacion CSV
- acciones contextuales

### Temas

- modo claro
- modo oscuro persistente

## 21. Tests

La suite cubre actualmente:

- creacion de bases
- relaciones
- importacion CSV
- orden por columnas
- duplicado de registros
- restauracion y eliminacion de archivados
- estadisticas
- y distintos flujos criticos de UI/backend

Ejecucion:

```powershell
.\.venv\Scripts\python manage.py test
```
