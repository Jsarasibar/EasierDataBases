# Guia de uso de EasierDataBases

Esta guia explica, paso a paso, como usar EasierDataBases desde el punto de vista de un usuario final.

## 1. Entrar al sistema

Al abrir EasierDataBases puedes:

- crear una cuenta,
- ingresar con una cuenta existente,
- o recuperar tu contrasena.

## 2. Entender el dashboard

El dashboard es tu punto de partida.

Hoy esta organizado asi:

- `Tus bases`
- `Accesos rapidos`
- `Resumen rapido`
- `Ideas para empezar`
- `Actividad reciente`

La seccion principal es `Tus bases`.

## 3. Crear una base

1. Haz clic en `Nueva base`.
2. Se abrira el asistente de creacion.

El asistente tiene 4 pasos:

1. elegir plantilla
2. poner nombre
3. completar estructura inicial
4. confirmar

En el paso 3 puedes:

- activar o desactivar campos base,
- sumar extras,
- activar `Prioridad`,
- y agregar campos propios.

## 4. Abrir una base

Cuando entras a una base veras estas pestanas:

- `Registros`
- `Trabajo diario`
- `Estadisticas`
- `Estructura`
- `Gestion`
- `Historial`

La vista que se abre por defecto es `Registros`.

## 5. Trabajar en `Registros`

Es la seccion principal para operar datos.

Aqui puedes:

- ver registros en tabla o tarjetas,
- buscar por ID, nombre o contenido,
- ordenar por columnas,
- filtrar,
- crear registros,
- editar,
- duplicar,
- archivar,
- o eliminar definitivamente.

### Busqueda

Hay una sola caja de busqueda.

Sirve para encontrar:

- un ID exacto,
- el nombre visible del registro,
- o cualquier contenido textual disponible.

### Orden por columnas

Haz clic sobre el nombre de una columna para ordenar.

Cada clic alterna entre:

- ascendente
- descendente

### Filtros avanzados

Dependiendo de la base, puedes filtrar por:

- seleccion,
- relacion,
- si/no,
- fechas,
- rangos numericos,
- prioridad.

### Menu `...` por registro

Cada registro tiene un menu de acciones.

Opciones actuales:

- `Editar`
- `Duplicar`
- `Archivar`
- `Eliminar`

`Eliminar` abre una confirmacion propia de la app y elimina el registro definitivamente.

## 6. Crear o editar registros

Para cargar un registro:

1. Ve a `Registros`.
2. Haz clic en `Agregar registro`.
3. Completa los campos.
4. Guarda.

El nombre visible del registro no es fijo: depende del campo principal que definas en `Estructura`.

## 7. Archivar y restaurar registros

### Archivar

Desde `Registros`, abre el menu `...` y elige `Archivar`.

El registro deja de verse en la base activa, pero no se pierde.

### Gestionar archivados

1. Ve a `Gestion`.
2. Abre la tarjeta `Archivados`.

Desde ahi puedes:

- restaurar un registro,
- eliminarlo definitivamente,
- restaurar todos,
- o eliminar todos.

## 8. Entender `Trabajo diario`

`Trabajo diario` es una vista mas liviana pensada para operar rapido.

Sirve para:

- ver lo importante del dia,
- entrar a registros prioritarios,
- y cargar rapido sin navegar tanto.

## 9. Usar `Estadisticas`

La pestana `Estadisticas` sirve para leer rapidamente que esta pasando en tu base.

Hoy incluye:

- resumen automatico,
- estadisticas utiles para operar,
- constructor de estadisticas,
- grafico o resultado,
- interpretacion,
- comparacion,
- y estadisticas guardadas.

### Como usarla

1. Entra en `Estadisticas`.
2. Elige un campo en `Constructor de estadisticas`.
3. Elige el tipo de grafico disponible.
4. Si quieres, abre `Opciones avanzadas`.
5. Haz clic en `Analizar`.

Si activas `Comparacion`, puedes comparar con:

- `Sin comparacion`
- `Ultimos 7 dias previos`
- `Ultimos 30 dias previos`
- `Comparacion manual`

## 10. Editar la estructura de una base

En `Estructura` puedes:

- agregar campos,
- editar campos,
- duplicarlos,
- moverlos arriba o abajo,
- crear relaciones,
- marcar si son obligatorios,
- decidir si se ven en la tabla,
- y cambiar la columna principal del registro.

### Cambiar el nombre visible del registro

En la parte superior de `Estructura` veras el bloque `Registro`.

Desde ahi puedes elegir que columna representa el nombre visible del registro.

## 11. Crear relaciones entre bases

Las relaciones sirven para conectar informacion entre bases.

Ejemplos:

- pedidos con clientes,
- alumnos con cursos,
- productos con proveedores.

### Como crear una relacion

1. Ve a `Estructura`.
2. Crea un campo nuevo.
3. Elige tipo `Relacion con otra base`.
4. Selecciona la base relacionada.
5. Guarda.

### Como usar una relacion al cargar un registro

Cuando aparece un campo de relacion:

- puedes buscar por ID o texto,
- elegir un registro existente,
- o crear uno nuevo sin salir del formulario.

## 12. Importar CSV

La importacion ahora es guiada en 2 pasos.

### Paso 1

1. Ve a `Gestion`.
2. En `Datos y operaciones`, sube tu archivo CSV.
3. Indica si tiene encabezados.
4. Haz clic en `Subir archivo y continuar`.

### Paso 2

1. Revisa la vista previa.
2. Mapea cada columna del archivo con el dato correcto.
3. Si una columna no sirve, dejala en `Ignorar`.
4. Confirma la importacion.

## 13. Exportar CSV

En `Gestion > Datos y operaciones`, usa `Exportar CSV`.

## 14. Gestionar equipo y permisos

En `Gestion > Equipo y permisos` puedes:

- ver quien tiene acceso,
- asignar administradores,
- y asignar editores.

Roles actuales:

- `Administrador`
- `Editor`

## 15. Cambiar nombre o eliminar una base

En `Gestion > Zona sensible` puedes:

- cambiar el nombre de la base,
- o ir al flujo de eliminacion segura.

## 16. Revisar el historial

En `Historial` puedes ver:

- que accion se hizo,
- quien la hizo,
- cuando ocurrio,
- y el detalle del cambio.

Si haces clic en el detalle, se abre una tarjeta con mas informacion.

En cambios de registros, puede verse el `antes / ahora`.

## 17. Modo oscuro y modo claro

La app tiene selector de tema en la barra superior.

El cambio:

- afecta toda la interfaz,
- se guarda,
- y se mantiene al navegar.
