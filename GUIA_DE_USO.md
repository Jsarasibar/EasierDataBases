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

## 2. Crear una nueva base

Desde el dashboard:

1. Haz clic en `Nueva base`.
2. Se abrira el asistente de creacion.

El asistente te va a guiar en 4 pasos.

### Paso 1. Elegir una plantilla

Aqui eliges con que estructura quieres empezar.

Opciones disponibles:

- `Productos / Inventario`
- `Alumnos / Cursos`
- `Clientes / Contactos`
- `Otra base`
- `Desde cero`

Cada plantilla ya trae campos basicos listos para usar.

Ejemplos:

- Productos: nombre, SKU, precio, stock, categoria.
- Alumnos: nombre, curso, email, telefono.
- Clientes: nombre, empresa, email, ultimo contacto.

Si no estas seguro, puedes elegir `Otra base` o `Desde cero`.

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

Aqui puedes:

- activar campos extra recomendados,
- cargar ejemplos para entender mejor como funciona,
- elegir si quieres empezar en modo simple o avanzado.

Si no quieres pensar demasiado al principio, conviene:

- dejar los ejemplos activados,
- y comenzar en `Modo simple`.

### Paso 4. Confirmar

Veras un resumen final de lo que se va a crear.

Si todo esta bien:

1. Revisa el nombre.
2. Revisa la plantilla.
3. Haz clic en confirmar.

La base quedara creada y lista para usar.

## 3. Entender la pantalla de una base

Cuando entras a una base, veras varias pestañas.

### Resumen

Muestra una vista general de la base:

- cuantos registros tiene,
- cuantos campos hay,
- cuantas relaciones existen,
- y que acciones conviene hacer despues.

Es una buena pestaña para ubicarse.

### Trabajo diario

Esta vista sirve para operar rapido.

Aqui puedes:

- ver elementos urgentes o importantes,
- abrir registros rapidamente,
- y entender como se veria la carga basica.

Es la mejor pestaña para uso cotidiano si no quieres entrar en configuraciones.

### Registros

Esta es la vista principal para trabajar con los datos.

Aqui puedes:

- buscar por nombre o contenido,
- filtrar por prioridad,
- ordenar registros,
- cambiar entre vista de tabla y tarjetas,
- guardar vistas,
- y agregar registros nuevos.

### Estructura

Esta pestaña sirve para diseñar la base.

Aqui puedes:

- ver todos los campos,
- editar nombres y ayudas,
- crear campos nuevos,
- crear listas de opciones,
- crear relaciones con otras bases,
- y revisar una vista previa del formulario.

Si eres administrador, podras modificar la estructura.

### Gestion

Sirve para tareas de administracion.

Aqui puedes:

- importar datos desde CSV,
- exportar la base,
- y asignar roles a otras personas.

## 4. Crear registros manualmente

Para cargar informacion manualmente:

1. Entra en la pestaña `Registros`.
2. Haz clic en `Agregar registro` o `Nuevo registro`.
3. Completa el nombre principal.
4. Completa los campos visibles.
5. Elige una prioridad si corresponde.
6. Guarda el registro.

Ejemplo en una base de productos:

- Nombre del registro: `Cafe molido`
- Precio: `1500`
- Stock: `12`
- Categoria: `Bebidas`
- Prioridad: `Urgente`

## 5. Buscar y filtrar informacion

Para encontrar datos rapidamente:

1. Ve a `Registros`.
2. Usa la caja de busqueda.
3. Si quieres, filtra por prioridad.
4. Elige el orden de visualizacion.

Puedes usar esto para cosas como:

- ver solo lo urgente,
- encontrar un cliente por nombre,
- revisar productos sin stock,
- o localizar un pedido puntual.

## 6. Guardar vistas frecuentes

Si usas mucho los mismos filtros:

1. Aplica una busqueda o filtro.
2. Escribe un nombre en `Guardar esta vista`.
3. Guarda.

Despues podras volver a usar esa vista con un clic.

Ejemplos de vistas utiles:

- `Urgentes`
- `Clientes activos`
- `Productos a reponer`
- `Pedidos recientes`

## 7. Editar la estructura de la base

Si quieres adaptar la base a tu negocio:

1. Ve a la pestaña `Estructura`.
2. Revisa los campos actuales.
3. Si necesitas uno nuevo, usa el formulario de `Nuevo campo`.

Al crear un campo, debes definir:

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

### Ejemplo de nuevos campos

En una base de productos podrias agregar:

- `Proveedor`
- `Costo`
- `Codigo de barras`

En una base de clientes:

- `Etapa comercial`
- `Vendedor responsable`
- `Origen`

## 8. Crear un campo de seleccion

Si quieres que un dato tenga opciones fijas:

1. En `Estructura`, crea un nuevo campo.
2. Elige tipo `Seleccion`.
3. En opciones, escribe una opcion por linea.

Ejemplo:

```text
Pendiente
En curso
Completado
```

Esto ayuda a mantener consistencia y evitar errores al cargar datos.

## 9. Relacionar una base con otra

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

## 10. Navegar relaciones en ambos sentidos

Cuando abras el detalle de un registro relacionado, EasierDataBases te mostrara:

- las relaciones salientes: a que otros registros apunta,
- las relaciones entrantes: que otros registros lo referencian.

Esto te ayuda a seguir la informacion sin perder contexto.

Ejemplo:

- abres un pedido,
- ves a que cliente pertenece,
- entras al cliente,
- y ves todos los pedidos asociados.

## 11. Importar datos desde CSV

Si ya tienes datos en Excel o en otra herramienta, puedes importarlos.

### Paso a paso

1. Ve a `Gestion`.
2. En `Importacion guiada`, selecciona tu archivo `.csv`.
3. Indica si el archivo tiene encabezados.
4. Haz clic en `Siguiente: mapear columnas`.
5. En la pantalla siguiente, relaciona cada columna con el dato correcto.
6. Confirma la importacion.

### Ejemplo de mapeo

Si tu CSV tiene:

- `Nombre`
- `Precio`
- `Stock`

Puedes mapear:

- `Nombre` -> `Nombre principal`
- `Precio` -> `Precio`
- `Stock` -> `Stock`

### Resultado

Al finalizar veras:

- cuantas filas se detectaron,
- cuantas se importaron,
- y si alguna fue omitida por error.

## 12. Exportar una base a CSV

Para sacar una copia de tus datos:

1. Ve a `Gestion`.
2. Haz clic en `Exportar CSV`.

Se descargara un archivo con:

- el nombre principal,
- la prioridad,
- y todos los campos visibles de la base.

## 13. Compartir la base con otras personas

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
- y gestionar miembros.

`Editor`

- puede trabajar con registros,
- pero no cambiar la estructura de la base.

## 14. Editar un registro existente

Para modificar datos ya cargados:

1. Entra en `Registros`.
2. Busca el elemento.
3. Haz clic en `Editar`.
4. Cambia los datos necesarios.
5. Guarda.

## 15. Eliminar un registro

Si un registro ya no sirve:

1. Entra en `Registros`.
2. Busca el elemento.
3. Haz clic en `Eliminar`.
4. Confirma.

Usa esta accion con cuidado.

## 16. Consejos para empezar bien

Si es tu primera base, conviene este orden:

1. Elige una plantilla parecida a tu caso.
2. Carga algunos registros de ejemplo.
3. Revisa la pestaña `Registros`.
4. Ajusta la estructura en `Estructura`.
5. Importa un CSV real cuando ya entiendas el modelo.

## 17. Buenas practicas

- Empieza simple. No intentes definir todo desde el primer dia.
- Usa nombres de campos claros y cortos.
- Usa campos de seleccion cuando quieras datos consistentes.
- Crea relaciones solo cuando de verdad conecten informacion.
- Guarda vistas si repites mucho la misma busqueda.
- Antes de importar muchos datos, prueba con un CSV chico.

## 18. Que no hace todavia EasierDataBases

En esta version, la herramienta no incluye todavia:

- automatizaciones avanzadas,
- dashboards,
- reportes complejos,
- permisos finos por campo,
- workflows empresariales avanzados.

La idea del producto hoy es resolver bien bases simples y operativas.

## 19. Ejemplo de primer recorrido recomendado

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
- navegacion entre datos,
- filtros,
- e importacion/exportacion.

## 20. Resumen final

Con EasierDataBases puedes:

- crear una base sin programar,
- personalizar sus campos,
- cargar y buscar registros,
- relacionar informacion,
- importar y exportar CSV,
- y trabajar con otras personas usando roles basicos.

La mejor forma de empezar es crear una primera base simple, usarla unos dias y luego ajustar su estructura segun tu necesidad real.
