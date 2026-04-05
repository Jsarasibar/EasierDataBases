# Guia paso a paso para crear y gestionar tu base de datos con EasierDataBases

Esta guia esta pensada para usuarios que quieren empezar a trabajar con EasierDataBases sin conocimientos tecnicos.

El objetivo es mostrar, paso a paso, como crear una base, personalizarla, cargar informacion y usarla en el trabajo diario.

## 1. Ingresar al sistema

Cuando abras EasierDataBases vas a poder:

- crear una cuenta nueva,
- ingresar con una cuenta existente,
- o recuperar tu contrasena si la olvidaste.

## 2. Entender el dashboard

El dashboard es tu punto de partida.

Hoy muestra:

- `Accesos rapidos`
- `Tus bases`
- `Ideas para empezar`
- `Actividad reciente`

`Tus bases` es la seccion principal del dashboard y el punto mas importante del producto.

## 3. Crear una nueva base

Desde el dashboard:

1. Haz clic en `Nueva base`.
2. Se abrira el asistente de creacion.

El asistente te guia en 4 pasos:

1. elegir plantilla
2. ponerle nombre
3. completar estructura inicial
4. confirmar

En el paso 3 puedes:

- activar o desactivar campos base,
- sumar extras,
- activar `Prioridad`,
- y agregar campos propios.

## 4. Entender la pantalla de una base

Cuando entras a una base, veras estas pestanas:

- `Registros`
- `Trabajo diario`
- `Estadisticas`
- `Estructura`
- `Gestion`
- `Historial`

## 5. Trabajar en `Registros`

Es la vista principal y la que se abre por defecto.

Aqui puedes:

- ver la tabla de datos,
- cambiar a vista de tarjetas,
- buscar por nombre, contenido o ID,
- ordenar tocando el nombre de una columna,
- aplicar filtros avanzados,
- abrir el menu `...` de cada registro,
- y agregar nuevos registros.

### Ordenar por columnas

Toca el encabezado de una columna para ordenar.

El orden cambia entre:

- ascendente
- descendente

### Filtros avanzados

En el panel derecho puedes abrir `Filtros avanzados`.

Dependiendo de los campos de la base, podras filtrar por:

- seleccion,
- si/no,
- relacion,
- rango numerico,
- rango de fechas.

### Menu `...` por registro

Cada registro en tabla o tarjetas tiene un menu de acciones.

Desde ahi puedes:

- `Duplicar`
- `Editar`
- `Eliminar`
- cambiar prioridad rapidamente si la base usa prioridad

## 6. Crear registros manualmente

Para cargar informacion manualmente:

1. Entra en `Registros`.
2. Haz clic en `Agregar registro`.
3. Completa los campos visibles.
4. Si la base usa prioridad, elige la prioridad.
5. Guarda el registro.

Importante:

- el nombre visible del registro sale del campo principal que definas en `Estructura`.

## 7. Cambiar la columna principal del registro

Cada base tiene una columna que define el nombre visible de cada registro.

Para cambiarla:

1. Ve a `Estructura`.
2. En el bloque superior `Registro`, busca `Columna que identifica cada registro`.
3. Elige otra columna.
4. Haz clic en `Actualizar columna`.

## 8. Editar la estructura de la base

En `Estructura` puedes:

- crear campos nuevos,
- editar campos existentes,
- duplicar campos,
- moverlos arriba o abajo,
- crear relaciones con otras bases,
- y cambiar la columna principal del registro.

### Reordenar campos

En cada tarjeta de campo puedes usar:

- `Subir`
- `Bajar`

Esto cambia el orden visual en formularios, tabla y detalle.

### Duplicar campos

Si necesitas un campo parecido a otro:

1. Ve a la tarjeta del campo.
2. Haz clic en `Duplicar`.

Se creara un nuevo campo con configuracion similar.

## 9. Relacionar una base con otra

Las relaciones sirven para conectar informacion.

Ejemplos:

- pedidos con clientes,
- alumnos con cursos,
- tareas con responsables,
- productos con proveedores.

### Como crear una relacion

1. Ve a `Estructura`.
2. Crea un nuevo campo.
3. Elige tipo `Relacion con otra base`.
4. Selecciona la base relacionada.
5. Guarda.

## 10. Buscar dentro de un campo de relacion

Cuando cargas o editas un registro y aparece un campo de relacion:

1. Usa la caja de busqueda del campo.
2. Escribe texto o un ID.
3. El sistema filtrara los registros disponibles de esa base relacionada.

## 11. Crear un registro relacionado sin salir del formulario

Si al cargar un registro todavia no existe el elemento relacionado:

1. En el campo de relacion, elige la opcion para agregar un nuevo registro relacionado.
2. Se abrira un modal dentro de la misma ventana.
3. Carga el nuevo registro.
4. Guarda.

Al cerrar el modal, ese nuevo registro quedara seleccionado automaticamente en el formulario original.

## 12. Ver estadisticas

En `Estadisticas` puedes analizar campos de tu base.

### Que ofrece hoy

- resumen automatico,
- estadisticas utiles para operar,
- analisis por campo,
- barras, torta, tabla o metricas,
- interpretacion textual,
- comparacion con periodos previos,
- guardado de estadisticas.

### Como usarla

1. Entra en `Estadisticas`.
2. En `Constructor de estadisticas`, elige un campo.
3. Elige el tipo de grafico disponible para ese campo.
4. Si quieres, abre `Opciones avanzadas`.
5. Haz clic en `Analizar`.

Si activas `Comparacion`, podras comparar con:

- ultimos 7 dias previos,
- ultimos 30 dias previos,
- comparacion manual.

## 13. Importar datos desde CSV

1. Ve a `Gestion`.
2. En `Importacion guiada`, selecciona tu archivo `.csv`.
3. Indica si el archivo tiene encabezados.
4. Continua para mapear columnas.
5. Relaciona cada columna con el dato correcto.
6. Confirma la importacion.

## 14. Exportar una base a CSV

1. Ve a `Gestion`.
2. Haz clic en `Exportar CSV`.

## 15. Compartir la base con otras personas

Si quieres trabajar con alguien mas:

1. Ve a `Gestion`.
2. Busca `Equipo y permisos`.
3. Escribe el nombre de usuario.
4. Elige un rol.
5. Guarda.

Roles disponibles:

- `Administrador`
- `Editor`

## 16. Revisar el historial de la base

1. Entra en la base.
2. Ve a `Historial`.
3. Revisa la tabla de movimientos.
4. Si quieres mas contexto, haz clic en `Ver detalle`.

Que puedes encontrar ahi:

- registros agregados,
- registros editados,
- registros duplicados,
- registros eliminados,
- cambios en estructura,
- importaciones,
- exportaciones,
- y cambios de permisos.

## 17. Resumen final

Con EasierDataBases puedes:

- crear una base sin programar,
- personalizar sus campos,
- elegir que columna representa al registro,
- cargar, duplicar, buscar y ordenar registros,
- filtrar por tipo de dato,
- relacionar informacion,
- buscar dentro de relaciones por ID o texto,
- crear registros relacionados sin salir del flujo,
- analizar tu base con estadisticas,
- revisar el historial de movimientos,
- importar y exportar CSV,
- y trabajar con otras personas usando roles basicos.
