# Guia paso a paso para crear y gestionar tu base de datos con EasierDataBases

Esta guia esta pensada para usuarios que quieren empezar a trabajar con EasierDataBases sin conocimientos tecnicos.

El objetivo es mostrar, paso a paso, como crear una base, personalizarla, cargar informacion y usarla en el trabajo diario.

## 1. Ingresar al sistema

Cuando abras EasierDataBases vas a poder:

- crear una cuenta nueva,
- ingresar con una cuenta existente,
- o recuperar tu contrasena si la olvidaste.

Si es tu primera vez:

1. Entra a la pantalla principal.
2. Haz clic en `Crear cuenta`.
3. Completa usuario, nombre, email y contrasena.
4. Una vez dentro, llegaras al dashboard.

## 2. Entender el dashboard

El dashboard es tu punto de partida.

Hoy muestra:

- `Accesos rapidos`
- `Tus bases`
- `Ideas para empezar`
- `Actividad reciente`

Desde ahi puedes:

- crear una base nueva,
- abrir una base existente,
- retomar registros recientes,
- o inspirarte con ejemplos de uso.

## 3. Crear una nueva base

Desde el dashboard:

1. Haz clic en `Nueva base`.
2. Se abrira el asistente de creacion.

El asistente te guia en 4 pasos.

### Paso 1. Elegir una plantilla

Aqui eliges con que estructura quieres empezar.

Opciones disponibles:

- `Productos / Inventario`
- `Alumnos / Cursos`
- `Clientes / Contactos`
- `Otra base`
- `Desde cero`

Cada plantilla ya trae campos base pensados para arrancar mas rapido.

Ejemplos:

- Productos: nombre, SKU, precio, stock, categoria.
- Alumnos: nombre, curso, email, telefono.
- Clientes: nombre, empresa, email, ultimo contacto.

### Paso 2. Ponerle nombre

En este paso defines:

- el nombre de tu base,
- y una descripcion breve de para que la usaras.

Ejemplos:

- `Catalogo de productos`
- `Seguimiento de alumnos`
- `Clientes activos`
- `Pedidos internos`

### Paso 3. Completarla

Este paso es la configuracion inicial real de la base.

Aqui veras:

- los campos base de la plantilla,
- campos extra recomendados,
- la opcion de activar `Prioridad`,
- y un bloque `+` para agregar campos propios.

Todos los campos se muestran en una misma grilla de seleccion.

Que puedes hacer aqui:

- dejar activados los campos base,
- marcar extras utiles,
- agregar un campo nuevo con su tipo,
- y decidir si quieres datos de ejemplo.

### Paso 4. Confirmar

Veras un resumen final de lo que se va a crear.

Si todo esta bien:

1. Revisa el nombre.
2. Revisa los campos elegidos.
3. Haz clic en confirmar.

La base quedara creada y lista para usar.

## 4. Entender la pantalla de una base

Cuando entras a una base, veras varias pestañas.

### Registros

Es la vista principal y la que se abre por defecto.

Aqui puedes:

- ver la tabla de datos,
- cambiar a vista de tarjetas,
- buscar por nombre, contenido o ID,
- filtrar,
- ordenar,
- y agregar nuevos registros.

La pantalla esta dividida en dos:

- a la izquierda la tabla o tarjetas,
- a la derecha los filtros y acciones.

### Trabajo diario

Esta vista sirve para operar rapido.

Aqui ves:

- los elementos importantes del dia,
- accesos rapidos para abrirlos,
- y el boton de carga rapida.

Es una pestaña pensada para el trabajo cotidiano, no para configurar estructura.

### Resumen

Muestra una vista general de la base:

- cuantos registros tiene,
- cuantos campos hay,
- cuantas relaciones existen,
- y acciones recomendadas.

Desde aqui tambien puedes entrar a `Graficos (estadisticas)`, que por ahora es una pantalla `Coming soon`.

### Estructura

Esta pestaña sirve para diseñar la base.

Aqui puedes:

- ver todos los campos,
- crear campos nuevos,
- editar los existentes,
- crear listas de opciones,
- crear relaciones con otras bases,
- y cambiar que columna se usa como nombre visible del registro.

La parte superior muestra el bloque `Registro`, donde eliges que columna representa el nombre principal de cada registro.

### Gestion

Sirve para tareas de administracion.

Aqui puedes:

- importar datos desde CSV,
- exportar la base,
- asignar roles a otras personas,
- y, si eres administrador, eliminar la base con confirmacion segura.

## 5. Crear registros manualmente

Para cargar informacion manualmente:

1. Entra en la pestaña `Registros`.
2. Haz clic en `Agregar registro` o `Nuevo registro`.
3. Completa los campos visibles.
4. Si la base usa prioridad, elige la prioridad.
5. Guarda el registro.

Importante:

- ya no existe un campo separado llamado `Nombre del registro`,
- el nombre visible del registro sale del campo principal que definas en `Estructura`.

Ejemplo en una base de productos:

- Nombre: `Cafe molido`
- Precio: `1500`
- Stock: `12`
- Categoria: `Bebidas`
- Prioridad: `Urgente` si esa base tiene prioridad activada

## 6. Buscar y filtrar informacion

Para encontrar datos rapidamente:

1. Ve a `Registros`.
2. Usa la caja de busqueda.
3. Si la base usa prioridad, filtra por prioridad.
4. Si quieres, usa el filtro `ID exacto`.
5. Elige el orden de visualizacion.

Puedes usar esto para cosas como:

- ver solo lo urgente,
- encontrar un cliente por nombre,
- localizar un registro por su ID interno,
- revisar productos sin stock,
- o ubicar un pedido puntual.

## 7. Cambiar la columna principal del registro

Cada base tiene una columna que define el nombre visible de cada registro.

Para cambiarla:

1. Ve a `Estructura`.
2. En el bloque superior `Registro`, busca `Columna que identifica cada registro`.
3. Elige otra columna.
4. Haz clic en `Actualizar columna`.

Esto hace que los registros pasen a mostrarse con el valor de esa columna.

Ejemplo:

- antes el registro se mostraba por `Nombre`,
- ahora puedes hacer que se muestre por `SKU` o por cualquier otro campo.

## 8. Editar la estructura de la base

Si quieres adaptar la base a tu negocio:

1. Ve a la pestaña `Estructura`.
2. Revisa los campos actuales.
3. Usa `Agregar campo o relacion` para sumar uno nuevo.
4. Usa `Editar` dentro de una tarjeta para modificar uno existente.

Al crear o editar un campo, puedes definir:

- nombre del campo,
- tipo,
- ayuda opcional,
- si es obligatorio,
- si debe verse en la tabla principal.

### Tipos de campo disponibles

Puedes crear campos de:

- texto,
- numero,
- moneda,
- si / no,
- fecha,
- email,
- telefono,
- seleccion,
- relacion con otra base.

## 9. Crear un campo de seleccion

Si quieres que un dato tenga opciones fijas:

1. En `Estructura`, crea o edita un campo.
2. Elige tipo `Seleccion`.
3. En opciones, escribe una opcion por linea.

Ejemplo:

```text
Pendiente
En curso
Completado
```

Esto ayuda a mantener consistencia y evitar errores al cargar datos.

## 10. Relacionar una base con otra

Las relaciones sirven para conectar informacion.

Ejemplos:

- pedidos con clientes,
- alumnos con cursos,
- tareas con responsables,
- productos con proveedores.

### Como crear una relacion

1. Crea o abre la base principal.
2. Ve a `Estructura`.
3. Crea un nuevo campo.
4. Elige tipo `Relacion con otra base`.
5. Selecciona la base relacionada.
6. Guarda.

Luego, cuando cargues un registro, podras elegir un elemento de la otra base.

### Ejemplo

Si tienes:

- una base `Clientes`
- y una base `Pedidos`

Puedes crear en `Pedidos` un campo `Cliente` que apunte a la base `Clientes`.

Despues, cada pedido podra vincularse a un cliente real.

## 11. Crear un registro relacionado sin salir del formulario

Si al cargar un registro todavia no existe el elemento relacionado:

1. En el campo de relacion, abre el selector.
2. Elige la opcion para agregar un nuevo registro relacionado.
3. Se abrira un modal dentro de la misma ventana.
4. Carga el nuevo registro.
5. Guarda.

Al cerrar el modal, ese nuevo registro quedara seleccionado automaticamente en el formulario original.

Esto es util, por ejemplo, si estas creando un pedido y todavia no existe el cliente.

## 12. Navegar relaciones en ambos sentidos

Cuando abras el detalle de un registro relacionado, EasierDataBases te mostrara:

- las relaciones salientes: a que otros registros apunta,
- las relaciones entrantes: que otros registros lo referencian.

Ademas, en la tabla de `Registros`, si haces clic sobre el valor de un campo relacionado, se abre una tarjeta contextual centrada con:

- nombre del registro relacionado,
- base a la que pertenece,
- algunos datos visibles,
- acceso para abrirlo o editarlo.

## 13. Importar datos desde CSV

Si ya tienes datos en Excel o en otra herramienta, puedes importarlos.

### Paso a paso

1. Ve a `Gestion`.
2. En `Importacion guiada`, selecciona tu archivo `.csv`.
3. Indica si el archivo tiene encabezados.
4. Haz clic en continuar para mapear columnas.
5. En la pantalla siguiente, relaciona cada columna con el dato correcto.
6. Confirma la importacion.

### Ejemplo de mapeo

Si tu CSV tiene:

- `Nombre`
- `Precio`
- `Stock`

Puedes mapear:

- `Nombre` -> `Nombre`
- `Precio` -> `Precio`
- `Stock` -> `Stock`

### Resultado

Al finalizar veras:

- cuantas filas se detectaron,
- cuantas se importaron,
- cuantas se omitieron,
- y algunos errores si hubo filas invalidas.

En relaciones, la importacion puede resolver por ID o por nombre unico. Si hay duplicados, te pedira usar el ID.

## 14. Exportar una base a CSV

Para sacar una copia de tus datos:

1. Ve a `Gestion`.
2. Haz clic en `Exportar CSV`.

Se descargara un archivo con:

- todos los campos visibles de la base,
- y `Prioridad` si esa base la usa.

## 15. Compartir la base con otras personas

Si quieres trabajar con alguien mas:

1. Ve a `Gestion`.
2. Busca la seccion `Equipo y permisos`.
3. Escribe el nombre de usuario.
4. Elige un rol.
5. Guarda.

### Roles disponibles

`Administrador`

- puede editar estructura,
- importar/exportar,
- gestionar miembros,
- y eliminar la base.

`Editor`

- puede trabajar con registros,
- pero no cambiar la estructura de la base.

## 16. Editar un registro existente

Para modificar datos ya cargados:

1. Entra en `Registros`.
2. Busca el elemento.
3. Haz clic en `Editar`.
4. Cambia los datos necesarios.
5. Guarda.

## 17. Eliminar un registro o una base

### Eliminar un registro

1. Entra en `Registros`.
2. Busca el elemento.
3. Haz clic en `Eliminar`.
4. Confirma.

### Eliminar una base

Si eres administrador:

1. Ve a `Gestion`.
2. Busca la zona sensible.
3. Elige eliminar la base.
4. Escribe el nombre exacto de la base.
5. Escribe `ELIMINAR`.
6. Confirma.

Esto evita borrados accidentales.

## 18. Ver estadisticas

En `Resumen` veras un acceso a `Graficos (estadisticas)`.

Hoy esa vista todavia no calcula estadisticas reales, pero anticipa lo que vendra:

- graficos por campos seleccionados,
- distribuciones,
- conteos,
- y resumenes reutilizables.

## 19. Consejos para empezar bien

Si es tu primera base, conviene este orden:

1. Elige una plantilla parecida a tu caso.
2. Deja algunos campos base activados.
3. Agrega solo los extras realmente utiles.
4. Carga algunos registros de ejemplo.
5. Revisa la pestaña `Registros`.
6. Ajusta la estructura en `Estructura`.
7. Importa un CSV real cuando ya entiendas el modelo.

## 20. Buenas practicas

- Empieza simple. No intentes definir todo desde el primer dia.
- Usa nombres de campos claros y cortos.
- Usa campos de seleccion cuando quieras datos consistentes.
- Crea relaciones solo cuando de verdad conecten informacion.
- Elige bien que columna identifica al registro.
- Antes de importar muchos datos, prueba con un CSV chico.

## 21. Que no hace todavia EasierDataBases

En esta version, la herramienta no incluye todavia:

- automatizaciones avanzadas,
- dashboards,
- reportes complejos,
- permisos finos por campo,
- workflows empresariales avanzados,
- estadisticas funcionales dentro del modulo de graficos.

La idea del producto hoy es resolver bien bases simples y operativas.

## 22. Ejemplo de primer recorrido recomendado

Si quieres aprender rapido, prueba este caso:

### Base 1. Clientes

Campos recomendados:

- Nombre
- Empresa
- Email
- Telefono

### Base 2. Pedidos

Campos recomendados:

- Fecha
- Estado
- Importe
- Cliente (relacion con Clientes)

Con estas dos bases puedes practicar:

- creacion de bases,
- campos personalizados,
- relaciones,
- carga de registros,
- creacion inline de relacionados,
- navegacion entre datos,
- filtros,
- e importacion/exportacion.

## 23. Resumen final

Con EasierDataBases puedes:

- crear una base sin programar,
- personalizar sus campos,
- elegir que columna representa al registro,
- cargar y buscar registros,
- relacionar informacion,
- crear registros relacionados sin salir del flujo,
- importar y exportar CSV,
- y trabajar con otras personas usando roles basicos.

La mejor forma de empezar es crear una primera base simple, usarla unos dias y luego ajustar su estructura segun tu necesidad real.
