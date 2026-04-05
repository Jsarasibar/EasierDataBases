# Manual Tecnico de EasierDataBases

## 1. Objetivo del documento

Este manual tecnico describe como funciona EasierDataBases a nivel funcional y tecnico.

La idea es que cualquier persona que tome el proyecto pueda entender:

- que resuelve el sistema,
- como esta organizado,
- cuales son sus entidades principales,
- como es el flujo interno de cada modulo,
- como se relacionan frontend, vistas, formularios y modelos,
- y que comportamiento esperar en cada seccion del producto.

## 2. Vision general del producto

EasierDataBases es una plataforma no-code construida con Django para crear y operar bases de datos simples desde una interfaz visual.

Hoy el producto permite:

- crear bases desde cero o con plantillas,
- definir campos personalizados,
- cargar, editar, duplicar y eliminar registros,
- relacionar bases entre si,
- importar y exportar CSV,
- analizar datos con estadisticas,
- trabajar con usuarios y roles basicos,
- y mantener un historial de actividad por base.

## 3. Stack tecnologico

- Python
- Django 6
- SQLite para desarrollo local
- PostgreSQL soportado mediante `DATABASE_URL`
- templates server-rendered de Django
- CSS propio
- JavaScript liviano embebido en templates

## 4. Estructura general del proyecto

- `config/`: configuracion del proyecto
- `app/`: dominio principal, modelos, vistas, formularios, urls y tests
- `templates/`: interfaz HTML
- `static/`: estilos y assets
- `tmp/`: archivos temporales de soporte

## 5. Arquitectura conceptual

La aplicacion se apoya sobre una idea central:

> una base creada por un usuario tiene su propia estructura y sus propios registros.

Cada base define:

- nombre y slug,
- si usa prioridad o no,
- sus campos,
- sus miembros,
- sus registros,
- sus estadisticas guardadas,
- y su historial.

## 6. Entidades principales del dominio

### `AppDatabase`

Representa una base creada por un usuario.

### `DatabaseMembership`

Define acceso y rol sobre cada base.

Roles actuales:

- `admin`
- `editor`

### `CustomField`

Representa un campo configurable dentro de una base.

Propiedades relevantes:

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

Reglas importantes:

- `key` no cambia despues de creado el campo
- `position` define el orden visual del campo
- si un campo ya tiene datos, no se permiten cambios destructivos
- si un campo relacion ya tiene datos, no se puede cambiar la base relacionada

### `Record`

Representa un registro dentro de una base.

Caracteristicas:

- pertenece a una base
- guarda sus datos en un `JSONField`
- puede tener prioridad si la base la usa
- mantiene un `title` sincronizado con el campo principal

### `DatabaseActivity`

Representa un movimiento de historial dentro de una base.

### `SavedStatistic`

Permite guardar configuraciones de analisis estadistico por base.

## 7. Flujo general del sistema

1. el usuario se registra o inicia sesion
2. entra al dashboard
3. crea una nueva base o abre una existente
4. define la estructura inicial mediante el asistente o el editor
5. carga registros manualmente o por CSV
6. opera sobre esos registros desde `Registros` o `Trabajo diario`
7. consulta `Estadisticas`
8. administra miembros, importaciones, exportaciones y cambios desde `Gestion`
9. revisa trazabilidad desde `Historial`

## 8. Dashboard

El dashboard es el centro de entrada al producto.

Secciones actuales:

- accesos rapidos
- tus bases
- ideas para empezar
- actividad reciente

`Tus bases` es la seccion principal.

## 9. Flujo de creacion de una base

La creacion de bases se hace mediante un asistente multi-paso:

1. elegir plantilla
2. definir nombre y descripcion
3. completar estructura inicial
4. confirmar

Al confirmar:

- se crea la base
- se crean los campos
- se marca el primer campo como principal si corresponde
- se crean registros demo si aplica
- se crea membresia admin para el creador
- se registra actividad en historial

## 10. Organizacion interna de una base

Orden actual de pestanas:

- `Registros`
- `Trabajo diario`
- `Estadisticas`
- `Estructura`
- `Gestion`
- `Historial`

### `Registros`

Es la vista principal de trabajo.

Muestra:

- tabla o tarjetas
- busqueda libre
- filtro por ID
- filtros avanzados dinamicos
- ordenamiento por columnas
- paginacion
- menu `...` por registro

Caracteristicas clave:

- encabezados clickeables con toggle ascendente / descendente
- acciones por registro:
  - duplicar
  - editar
  - eliminar
  - cambiar prioridad rapidamente
- preservacion de filtros y posicion vertical tras submits

### `Trabajo diario`

Vista operativa mas liviana para concentrar accesos y trabajo inmediato.

### `Estadisticas`

Modulo analitico de la base.

Estructura interna actual:

1. resumen automatico
2. estadisticas utiles para operar
3. workspace principal:
   - constructor
   - grafico o resultado
   - interpretacion
4. comparacion
5. estadisticas guardadas

### `Estructura`

Editor visual de la base.

Permite:

- crear, editar y duplicar campos
- moverlos arriba o abajo
- definir relaciones
- elegir si se muestran en tabla
- elegir obligatoriedad
- ajustar ayuda
- definir que columna es el nombre visible del registro

### `Gestion`

Incluye:

- importacion CSV
- exportacion CSV
- miembros y roles
- cambio de nombre de base
- eliminacion segura de base

### `Historial`

Muestra:

- accion
- detalle
- usuario
- fecha
- payload enriquecido
- comparacion `antes / ahora` si hubo cambios

## 11. Flujo de registros

### Creacion y edicion

La pantalla de alta y edicion se construye dinamicamente segun los `CustomField` de la base.

El formulario:

- construye widgets segun tipo
- agrega selector de prioridad si aplica
- valida formatos especificos
- valida relaciones permitidas

Si el campo es de relacion, el formulario agrega una caja de busqueda para encontrar registros por ID o texto y mantiene la opcion de alta inline.

### Duplicado

Existe una accion dedicada de duplicado.

Comportamiento:

- copia `data`
- copia prioridad si aplica
- regenera PK y timestamps
- si el campo principal es textual, prefija `Copia de ...`
- registra actividad en historial

### Campo principal del registro

Cada base puede elegir que `CustomField` es el principal.

Ese campo:

- define el nombre visible del registro
- se usa en tablas, tarjetas, previews y relaciones

## 12. Relaciones entre bases

Las relaciones se modelan mediante `CustomField` de tipo `relation`.

Internamente:

- en `Record.data` se guarda el ID del registro relacionado
- no se usa una columna FK fija en SQL por cada relacion

### Busqueda en relaciones

El formulario de registros aporta:

- filtro local de opciones del select
- busqueda por ID o texto
- endpoint de apoyo para coincidencias remotas

### Restricciones

- solo se muestran bases visibles para el usuario
- solo se permiten registros relacionados de bases accesibles
- el backend valida que no se puedan forzar IDs ajenos

## 13. Importacion y exportacion CSV

### Importacion

Pasos:

1. upload del archivo
2. lectura segura temporal
3. preview de encabezados y filas
4. pantalla de mapeo de columnas
5. procesamiento completo
6. resumen final

### Exportacion

La exportacion:

- genera CSV de la base actual
- usa nombres visibles de campos
- resuelve relaciones con su valor visible

## 14. Historial y trazabilidad

Eventos que hoy generan historial:

- creacion de base
- renombre de base
- creacion, edicion, duplicado y eliminacion de registros
- alta, edicion, duplicado, movimiento y baja de campos
- cambio del campo principal
- importaciones y exportaciones
- cambios de membresia
- cambios rapidos de prioridad

## 15. Frontend y comportamiento visual

La aplicacion esta renderizada del lado servidor.

Interacciones JS actuales mas relevantes:

- cambio de tema claro / oscuro
- restauracion de scroll al enviar formularios dentro de bases
- modales de preview
- apertura de historiales
- apertura de relaciones
- selector dinamico de tipos de grafico
- mostrar/ocultar comparacion manual
- expansion del grafico de estadisticas
- cierre de menus `...`
- filtrado de relaciones en formularios

## 16. Sistema de estadisticas en detalle

La seccion de estadisticas trabaja sobre:

- la base actual
- los registros visibles para el usuario
- filtros seleccionados
- el campo elegido

Segun el tipo de campo:

- un campo categorico muestra barras, torta o tabla
- un campo numerico muestra metricas o tabla

La comparacion permite:

- comparar contra 7 dias previos
- comparar contra 30 dias previos
- comparar manualmente con otro rango

## 17. Seguridad y controles de integridad

- `CustomField.key` estable
- cambios de tipo restringidos si hay datos
- cambio de base relacionada bloqueado si ya hay datos
- borrado de campo bloqueado si tiene datos
- sincronizacion de `title` cuando cambia el campo principal
- autenticacion Django
- membresia por base
- validacion backend de IDs relacionados

## 18. Tests y calidad actual

Los tests actuales cubren principalmente:

- autenticacion
- creacion de base
- plantillas
- relaciones
- importacion CSV
- restricciones de permisos
- historial
- estadisticas
- cambios de estructura
- reordenamiento de campos
- duplicado de registros
- orden y filtros avanzados

## 19. Archivos tecnicos mas importantes

- `C:\Users\mergo\Desktop\Archivos\Proyectos\EasierDataBases\config\settings.py`
- `C:\Users\mergo\Desktop\Archivos\Proyectos\EasierDataBases\app\models.py`
- `C:\Users\mergo\Desktop\Archivos\Proyectos\EasierDataBases\app\views.py`
- `C:\Users\mergo\Desktop\Archivos\Proyectos\EasierDataBases\app\forms.py`
- `C:\Users\mergo\Desktop\Archivos\Proyectos\EasierDataBases\app\urls.py`
- `C:\Users\mergo\Desktop\Archivos\Proyectos\EasierDataBases\app\tests.py`
- `C:\Users\mergo\Desktop\Archivos\Proyectos\EasierDataBases\templates\base.html`
- `C:\Users\mergo\Desktop\Archivos\Proyectos\EasierDataBases\templates\database_detail.html`
- `C:\Users\mergo\Desktop\Archivos\Proyectos\EasierDataBases\templates\record_form.html`
- `C:\Users\mergo\Desktop\Archivos\Proyectos\EasierDataBases\static\styles\app.css`
