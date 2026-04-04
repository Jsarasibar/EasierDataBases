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

No es un manual de usuario final. Es una guia para desarrollo, mantenimiento, debugging, onboarding y evolucion del producto.

---

## 2. Vision general del producto

EasierDataBases es una plataforma no-code construida con Django para crear y operar bases de datos simples desde una interfaz visual.

El objetivo del producto es ubicarse entre:

- una planilla flexible pero desordenada,
- y un sistema mas estructurado pero demasiado complejo para usuarios no tecnicos.

Hoy el producto permite:

- crear bases desde cero o con plantillas,
- definir campos personalizados,
- cargar, editar y eliminar registros,
- relacionar bases entre si,
- importar y exportar CSV,
- analizar datos con estadisticas,
- trabajar con usuarios y roles basicos,
- y mantener un historial de actividad por base.

El proyecto esta pensado actualmente como:

- MVP avanzado,
- apto para demos comerciales,
- apto para pilotos cerrados,
- y base de una evolucion hacia un SaaS generalista.

---

## 3. Stack tecnologico

### Backend

- Python
- Django 6
- SQLite para desarrollo local
- PostgreSQL soportado para entornos productivos mediante `DATABASE_URL`

### Frontend

- Templates server-rendered de Django
- CSS propio
- JavaScript liviano embebido en templates para interacciones puntuales

### Dependencias principales

- `Django`
- `dj-database-url`
- `psycopg[binary]`

---

## 4. Estructura general del proyecto

### Raiz del proyecto

- `manage.py`: punto de entrada para tareas Django
- `README.md`: documentacion general
- `GUIA_DE_USO.md`: guia funcional para usuarios
- `PROXIMAS_ACTUALIZACIONES.md`: roadmap
- `MANUAL_TECNICO.md`: este documento

### Directorios principales

- `config/`
  - configuracion del proyecto Django
  - settings, urls globales, wsgi/asgi

- `app/`
  - dominio principal del sistema
  - modelos, vistas, formularios, urls, tests, migraciones, filtros auxiliares

- `templates/`
  - interfaz HTML renderizada desde servidor

- `static/`
  - CSS y assets visuales

- `tmp/`
  - archivos temporales usados por flujos como importacion CSV

---

## 5. Arquitectura conceptual del producto

La aplicacion se apoya sobre una idea central:

> una base creada por un usuario tiene su propia estructura y sus propios registros.

Cada base define:

- su nombre,
- su identificador de URL,
- si usa prioridad o no,
- sus campos,
- sus miembros,
- sus registros,
- sus estadisticas guardadas,
- y su historial.

Desde esa base se derivan todos los flujos de trabajo.

---

## 6. Entidades principales del dominio

## 6.1 `AppDatabase`

Representa una base creada por un usuario.

Responsabilidades:

- almacenar nombre y slug,
- identificar si la base usa prioridad,
- actuar como contenedor de campos, registros, membresias e historial,
- servir como unidad funcional de aislamiento.

Cada base es hoy la unidad principal del producto.

## 6.2 `DatabaseMembership`

Define que usuarios tienen acceso a una base y con que rol.

Roles actuales:

- `admin`
- `editor`

Responsabilidades:

- permitir o denegar acceso a una base,
- controlar acciones administrativas,
- filtrar relaciones visibles entre bases.

## 6.3 `CustomField`

Representa un campo configurable dentro de una base.

Tipos soportados:

- texto
- numero
- moneda
- fecha
- si/no
- email
- telefono
- seleccion
- relacion con otra base

Propiedades relevantes:

- `label`: nombre visible
- `key`: identificador tecnico estable
- `field_type`
- `required`
- `show_in_table`
- `help_text`
- `is_primary`: indica si es la columna principal del registro
- `options_text`: opciones en campos de seleccion
- `relation_database`: base objetivo en campos relacion

Reglas importantes:

- `key` no cambia despues de creado el campo
- si un campo ya tiene datos, no se permiten cambios destructivos
- si un campo relacion ya tiene datos, no se puede cambiar la base relacionada

## 6.4 `Record`

Representa un registro dentro de una base.

Caracteristicas:

- pertenece a una base
- guarda sus datos en un `JSONField`
- puede tener prioridad si la base la usa
- mantiene un `title` sincronizado con el campo principal de la base

La data variable de los registros vive en `Record.data`, usando `CustomField.key` como clave.

## 6.5 `DatabaseActivity`

Representa un movimiento de historial dentro de una base.

Guarda:

- accion realizada
- detalle
- usuario
- fecha
- payload enriquecido para mostrar mas contexto

Sirve para trazabilidad y debugging funcional.

## 6.6 `SavedStatistic`

Permite guardar configuraciones de analisis estadistico por base.

Guarda:

- nombre de la estadistica
- campo analizado
- tipo de grafico
- filtros
- contexto de analisis

## 6.7 `SavedView`

Es una entidad heredada de una etapa anterior del MVP.

Hoy ya no es central en la interfaz principal, pero puede seguir presente por compatibilidad y evolucion futura.

---

## 7. Flujo general de uso del sistema

El flujo principal del producto hoy puede resumirse asi:

1. el usuario se registra o inicia sesion
2. entra al dashboard
3. crea una nueva base o abre una existente
4. define la estructura inicial mediante el asistente o el editor de estructura
5. carga registros manualmente o por CSV
6. opera sobre esos registros desde `Registros` o `Trabajo diario`
7. consulta `Estadisticas`
8. administra miembros, importaciones, exportaciones y cambios desde `Gestion`
9. revisa trazabilidad desde `Historial`

---

## 8. Flujo de autenticacion

Pantallas involucradas:

- registro
- login
- recuperacion de contrasena
- confirmacion de nueva contrasena

Comportamiento:

- un usuario puede crear cuenta desde la landing
- al ingresar correctamente es enviado al dashboard
- el header cambia segun autenticacion
- el logout se hace con formulario POST

La aplicacion usa el sistema de autenticacion estándar de Django.

---

## 9. Dashboard

El dashboard es el centro de entrada al producto una vez autenticado.

Objetivos del dashboard:

- mostrar accesos rapidos,
- dar protagonismo a `Tus bases`,
- ofrecer contexto reciente,
- y facilitar la creacion de nuevas bases.

Secciones actuales:

- accesos rapidos
- tus bases
- ideas para empezar
- actividad reciente

`Tus bases` es la seccion principal.

Desde ahi se accede al flujo central del producto.

---

## 10. Flujo de creacion de una base

La creacion de bases se hace mediante un asistente multi-paso.

### Paso 1. Elegir plantilla

Plantillas actuales:

- productos / inventario
- alumnos / cursos
- clientes / contactos
- otra base
- desde cero

Objetivo:

- reducir decisiones iniciales,
- ofrecer campos base razonables,
- y acelerar el primer uso.

### Paso 2. Definir nombre y descripcion

El usuario ingresa:

- nombre de la base
- descripcion funcional

El wizard conserva esa informacion entre pasos.

### Paso 3. Completar estructura inicial

Se muestran:

- campos base de plantilla
- extras sugeridos
- opcion de prioridad
- opcion de agregar campos personalizados

Todos los campos aparecen en una sola UI unificada con checkboxes.

La idea de este paso es que el usuario entienda:

> aqui estoy configurando mi base inicial

### Paso 4. Confirmar

Se presenta un resumen de:

- nombre
- descripcion
- campos elegidos
- configuracion adicional

Al confirmar:

- se crea la base
- se crean los campos
- se marca el primer campo como principal si corresponde
- se crean registros demo si el usuario los solicito
- se crea membresia admin para el creador
- se registra actividad en historial

---

## 11. Organizacion interna de una base

Cada base abierta se organiza en pestañas para reducir complejidad.

Orden actual:

- `Registros`
- `Trabajo diario`
- `Estadisticas`
- `Estructura`
- `Gestion`
- `Historial`

Cada una tiene un objetivo distinto.

## 11.1 `Registros`

Es la vista principal de trabajo.

Muestra:

- tabla o tarjetas
- filtro por ID
- busqueda libre
- filtros por prioridad si aplica
- ordenamiento
- paginacion

Objetivo:

- operar datos,
- no configurar estructura.

Caracteristicas:

- tabla a la izquierda
- panel de filtros y acciones a la derecha
- posibilidad de abrir previews de relaciones
- posibilidad de ir al detalle del registro

## 11.2 `Trabajo diario`

Es una vista operativa mas liviana.

Objetivo:

- mostrar lo prioritario del dia,
- facilitar acceso a registros importantes,
- y ofrecer una carga rapida.

No esta pensada para configuracion sino para operacion cotidiana.

## 11.3 `Estadisticas`

Es el modulo analitico de la base.

Su objetivo es mostrar:

- resumen automatico,
- indicadores operativos,
- analisis por campo,
- interpretacion,
- comparacion entre periodos,
- y configuraciones guardadas.

### Estructura interna actual

1. resumen automatico
2. estadisticas utiles para operar
3. workspace principal:
   - constructor
   - grafico o resultado
   - interpretacion
4. comparacion
5. estadisticas guardadas

### Constructor de estadisticas

Elementos basicos:

- seleccionar campo
- tipo de grafico

Elementos avanzados:

- buscar dentro de registros
- prioridad
- desde
- hasta

Comparacion:

- sin comparacion
- ultimos 7 dias previos
- ultimos 30 dias previos
- comparacion manual

### Tipos de analisis soportados

Segun el tipo de campo:

- distribucion
- tabla
- torta
- barras
- metricas numericas

### Tipos de lectura soportados

- conteos por valor
- peso relativo
- suma, promedio, minimo y maximo
- lectura automatica del resultado
- indicadores operativos
- comparacion de periodos

### Estadisticas guardadas

Permiten guardar analisis por base para reutilizarlos.

## 11.4 `Estructura`

Es el editor visual de la base.

Permite:

- ver todos los campos
- editar campos existentes
- crear nuevos campos
- definir relaciones
- definir si se muestran en tabla
- definir obligatoriedad
- ajustar ayuda
- y elegir que columna es el nombre visible del registro

Elementos clave:

- bloque superior `Registro`: selector de columna principal
- tarjetas por campo
- formularios inline de edicion
- boton controlado para crear nuevo campo

Reglas importantes:

- no se puede borrar un campo con datos existentes
- no se puede cambiar destructivamente un campo con datos
- la base relacionada no puede cambiarse si ya hay datos

## 11.5 `Gestion`

Agrupa tareas administrativas.

Incluye:

- importacion CSV
- exportacion CSV
- miembros y roles
- cambio de nombre de base
- eliminacion segura de base

### Importacion CSV

Flujo:

1. subir archivo
2. detectar encabezados y preview
3. mapear columnas
4. importar filas completas
5. mostrar resumen

### Zona sensible

Visible para admin.

Incluye:

- cambio de nombre
- eliminacion segura

La eliminacion exige confirmacion explicita.

## 11.6 `Historial`

Muestra todos los movimientos de la base.

Cada item muestra:

- accion
- detalle
- usuario
- fecha

Y puede abrir una tarjeta ampliada con:

- resumen
- descripcion
- payload enriquecido
- comparacion `antes / ahora` si hubo cambios

---

## 12. Flujo de registros

## 12.1 Creacion de un registro

La pantalla de alta se construye dinamicamente en funcion de los `CustomField` de la base.

El formulario:

- lee los campos activos de la base
- construye widgets segun tipo
- agrega selector de prioridad si la base la usa
- valida formatos especificos
- valida relaciones permitidas

Al guardar:

- serializa datos en `Record.data`
- calcula `title` a partir del campo principal
- crea historial

## 12.2 Edicion de un registro

El flujo es similar al de alta, pero:

- precarga valores existentes
- compara estado viejo y nuevo
- registra diferencias en historial

## 12.3 Eliminacion de un registro

Se hace con confirmacion previa y registra actividad.

## 12.4 Campo principal del registro

Cada base puede elegir que `CustomField` es el principal.

Ese campo:

- define el nombre visible del registro
- se usa en tablas, tarjetas, previews y relaciones

Si cambia el campo principal:

- se resincronizan los titulos de los registros existentes

---

## 13. Relaciones entre bases

Las relaciones se modelan mediante `CustomField` de tipo `relation`.

### Como se define una relacion

1. el usuario crea o edita un campo
2. selecciona tipo `relacion con otra base`
3. elige una base visible y autorizada

### Como se guarda una relacion

Internamente:

- en `Record.data` se guarda el ID del registro relacionado
- no se usa una columna FK fija en SQL por cada relacion

Esto hace al modelo flexible para bases dinamicas.

### Como se resuelve una relacion

Al mostrar el valor:

- se toma el ID guardado
- se busca el registro de la base relacionada
- se devuelve el `title` del registro relacionado

### Relaciones salientes y entrantes

Salientes:

- las definidas por los campos del registro actual

Entrantes:

- se reconstruyen buscando otros registros que apunten a este

### Navegacion relacionada

Actualmente existe:

- tarjeta contextual al hacer clic sobre el valor relacionado
- vista detalle del registro relacionado
- creacion de relacionado sin salir del formulario actual

### Restricciones

- solo se muestran bases visibles para el usuario
- solo se permiten registros relacionados de bases accesibles
- el backend valida que no se puedan forzar IDs ajenos

---

## 14. Importacion y exportacion CSV

## 14.1 Importacion

El flujo actual evita los errores mas comunes del MVP temprano.

Pasos:

1. upload del archivo
2. lectura segura temporal
3. preview de encabezados y filas
4. pantalla de mapeo de columnas
5. procesamiento completo
6. resumen final

Validaciones:

- campos obligatorios
- relaciones por ID o nombre
- deteccion de ambiguedad
- control de filas omitidas

## 14.2 Exportacion

La exportacion:

- genera CSV de la base actual
- usa nombres visibles de campos
- resuelve relaciones con su valor visible

---

## 15. Historial y trazabilidad interna

Cada accion importante registra una actividad.

Eventos que hoy suelen generar historial:

- creacion de base
- renombre de base
- creacion, edicion y eliminacion de registros
- alta, edicion y baja de campos
- cambio del campo principal
- importaciones y exportaciones
- cambios de membresia

El historial usa un payload enriquecido para:

- mostrar resúmenes
- representar cambios `antes / ahora`
- alimentar modales de detalle

---

## 16. Frontend y comportamiento visual

La aplicacion esta renderizada del lado servidor.

No hay frontend separado tipo SPA.

### Filosofia actual

- HTML server-rendered
- CSS propio
- JavaScript puntual para interacciones pequeñas

### Interacciones JS actuales mas relevantes

- cambio de tema claro / oscuro
- restauracion de scroll al enviar formularios dentro de bases
- modales de preview
- apertura de historiales
- apertura de relaciones
- selector dinamico de tipos de grafico
- mostrar/ocultar comparacion manual
- expand/collapse de detalles
- expansion del grafico de estadisticas

Esto mantiene el sistema relativamente simple de mantener.

---

## 17. Dark mode

El tema oscuro:

- se aplica a nivel global
- se guarda en `localStorage`
- se activa antes del render para evitar parpadeos

Impacta:

- layout general
- dashboard
- bases
- tablas
- modales
- estructura
- historial
- estadisticas

---

## 18. Restauracion de posicion vertical

Uno de los comportamientos recientes importantes es la restauracion de scroll.

Problema resuelto:

- al hacer submit dentro de una base, la pagina se refrescaba y volvía arriba

Solucion actual:

- en `base.html` se guarda `window.scrollY` en `sessionStorage`
- al volver a cargar una pagina de base, se restaura la posicion

Esto mejora mucho la experiencia en:

- estadisticas
- estructura
- gestion
- historial

---

## 19. Sistema de estadisticas en detalle

La seccion de estadisticas es hoy uno de los modulos mas ricos del sistema.

### 19.1 Entrada del modulo

El analizador parte de:

- la base actual
- los registros visibles para el usuario
- filtros seleccionados
- el campo elegido

### 19.2 Seleccion de visualizacion

Segun el tipo de campo:

- un campo categorico muestra barras, torta o tabla
- un campo numerico muestra metricas o tabla
- campos no analizables quedan en estado vacio

### 19.3 Resumen automatico

Muestra primero lo importante sin necesidad de configurar nada.

### 19.4 Estadisticas operativas

Apuntan a ayudar en decisiones concretas:

- vacios
- faltantes
- volumen
- actividad

### 19.5 Interpretacion

Es una lectura textual del resultado actual.

No reemplaza el grafico, pero ayuda a usuarios no tecnicos a entenderlo.

### 19.6 Comparacion

La comparacion permite:

- comparar contra 7 dias previos
- comparar contra 30 dias previos
- comparar manualmente con otro rango

Muestra:

- valor actual
- valor comparado
- diferencia
- variacion porcentual
- detalle por dato

### 19.7 Vista ampliada

El panel del grafico puede expandirse a un modal grande para mejorar lectura.

---

## 20. Seguridad y controles de integridad

El sistema ya incluye varias protecciones importantes.

### Integridad de datos

- `CustomField.key` estable
- cambios de tipo restringidos si hay datos
- cambio de base relacionada bloqueado si ya hay datos
- borrado de campo bloqueado si tiene datos
- sincronizacion de `title` cuando cambia el campo principal

### Seguridad de acceso

- autenticacion Django
- membresia por base
- roles basicos
- relaciones filtradas por acceso visible
- validacion backend de IDs relacionados

### Seguridad operativa

- importacion CSV controlada
- configuracion por variables de entorno
- settings preparados para produccion

---

## 21. Tests y calidad actual

La base de codigo tiene tests automatizados para flujos clave.

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

Comandos principales:

```powershell
.\.venv\Scripts\python manage.py test
.\.venv\Scripts\python manage.py check
```

---

## 22. Limitaciones actuales

Aunque el proyecto ya es funcional, todavia no cubre todo el alcance de un producto maduro.

Limitaciones actuales:

- no hay automatizaciones complejas
- no hay dashboards multiwidget completos
- no hay permisos finos por campo
- no hay organizaciones o workspaces explicitos
- no hay API publica separada
- no hay frontend desacoplado
- la analitica sigue evolucionando

---

## 23. Flujo tecnico resumido por capas

### Capa 1. Request

El navegador envia una request a una ruta Django.

### Capa 2. URL

`app/urls.py` o `config/urls.py` resuelven la vista correspondiente.

### Capa 3. View

La vista:

- valida permisos
- prepara queryset
- procesa formularios si aplica
- arma contexto
- renderiza template o redirige

### Capa 4. Forms

Los formularios:

- validan datos de entrada
- resuelven reglas de negocio cercanas a UI
- construyen formularios dinamicos

### Capa 5. Models

Los modelos:

- persisten la informacion
- encapsulan parte de la logica de representacion
- permiten componer consultas y relaciones

### Capa 6. Templates

Los templates:

- renderizan HTML final
- activan interacciones ligeras con JS
- consumen filtros y helpers

### Capa 7. CSS y JS

Aplican:

- diseño visual
- animaciones
- comportamiento interactivo puntual

---

## 24. Recomendaciones para tocar el proyecto sin romperlo

### Si vas a tocar `CustomField`

- no permitas cambiar `key` despues de creado
- revisa siempre impacto en `Record.data`

### Si vas a tocar relaciones

- valida acceso por membresia
- revisa importacion CSV
- revisa previews y detalles

### Si vas a tocar `Record.title`

- ten en cuenta el campo principal
- resincroniza registros existentes si cambia el campo de referencia

### Si vas a tocar `Estadisticas`

- valida tanto visualizacion como interpretacion
- revisa consistencia entre texto, barras y torta
- evita romper los flujos guardados

### Si vas a tocar templates grandes

- `database_detail.html` concentra mucha funcionalidad
- conviene hacer cambios pequeños y probar despues de cada bloque

---

## 25. Estado actual del proyecto

Hoy EasierDataBases puede describirse como:

- un MVP avanzado,
- generalista,
- usable para demos y pilotos,
- con una base tecnica ya bastante firme,
- y con un producto que resuelve de verdad la idea principal.

No es todavia una plataforma enterprise ni un SaaS masivo listo para escala grande, pero ya tiene:

- valor de producto,
- estructura coherente,
- interfaz trabajada,
- y una arquitectura razonable para seguir creciendo.

---

## 26. Archivos tecnicos mas importantes para entender el sistema

- `C:\Users\mergo\Desktop\Archivos\Proyectos\EasierDataBases\config\settings.py`
- `C:\Users\mergo\Desktop\Archivos\Proyectos\EasierDataBases\app\models.py`
- `C:\Users\mergo\Desktop\Archivos\Proyectos\EasierDataBases\app\views.py`
- `C:\Users\mergo\Desktop\Archivos\Proyectos\EasierDataBases\app\forms.py`
- `C:\Users\mergo\Desktop\Archivos\Proyectos\EasierDataBases\app\urls.py`
- `C:\Users\mergo\Desktop\Archivos\Proyectos\EasierDataBases\app\tests.py`
- `C:\Users\mergo\Desktop\Archivos\Proyectos\EasierDataBases\templates\base.html`
- `C:\Users\mergo\Desktop\Archivos\Proyectos\EasierDataBases\templates\database_detail.html`
- `C:\Users\mergo\Desktop\Archivos\Proyectos\EasierDataBases\static\styles\app.css`

---

## 27. Cierre

Este manual busca servir como mapa general del proyecto.

Si alguien nuevo entra a EasierDataBases, deberia poder usar este documento para:

- entender el producto,
- entender los modulos,
- ubicar la logica principal,
- y tocar el codigo con mas seguridad.

La recomendacion es mantener este archivo vivo a medida que el proyecto evolucione.
