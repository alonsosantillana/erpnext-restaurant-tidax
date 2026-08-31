## Context

`RestaurantObject.add_order()` crea la orden de mesa sin asignar `guest_count`,
por lo que el campo entero queda en cero. El Desk Form de comensales declara un
`Int` con default visual `1`, y `TableOrder.edit()` corrige el valor solo al abrir
el modal. Eso crea una diferencia entre el documento real y la interfaz.

Graphify ubica `RestaurantObject`, `TableOrder` y `table-order-class.js` en las
comunidades que participan en este flujo. La revision del codigo confirma que
delivery/recojo usa otra ruta y asigna cero de forma explicita.

## Decisions

### Valor autoritativo desde el servidor

`RestaurantObject.add_order()` asignara `guest_count = 1` antes de guardar. El
DocType tambien declarara default `1` para que otros flujos de nueva orden Dine In
partan del mismo valor. La ruta de pedidos externos mantiene su asignacion
explicita a cero.

### Selector derivado de la mesa

El Desk Form usara un campo `Select`. Al abrirlo, el cliente generara opciones
desde `1` hasta la capacidad `no_of_seats`. El maximo tambien incluira el valor
actual si es mayor, evitando perder datos por una reduccion posterior de
capacidad. Si no hay capacidad valida, se mostrara al menos `1`.

### Validacion

El formulario sera obligatorio y el servidor continuara aplicando la validacion
existente que exige un valor mayor que cero al facturar una orden Dine In.

## Files

- `restaurant_management/doctype/table_order/table_order.json`
- `restaurant_management/doctype/restaurant_object/restaurant_object.py`
- `restaurant_management/desk_form/restaurant_order_guest_count/restaurant_order_guest_count.json`
- `public/restaurant/js/table-order-class.js`
- pruebas de `Restaurant Object` y/o `Table Order`

No se modifican hooks, fixtures, APIs publicas ni reportes.

## Risks and Mitigations

- Capacidad vacia o cero: ofrecer siempre la opcion `1`.
- Orden historica sobre capacidad: incluir el valor actual en las opciones.
- Regresion en pedidos externos: conservar la asignacion explicita a cero y
  cubrirla mediante revision/prueba existente.
- Assets en cache: compilar la app y limpiar cache en el sitio autorizado.

## Rollback

Revertir los cuatro cambios funcionales devuelve la inicializacion y el campo
entero anteriores. No hay migracion ni datos que revertir.
