## Design

`Restaurant Company Settings` almacenará `pos_opening_series` y
`pos_closing_series`. Los valores usarán la sintaxis nativa de Frappe, por ejemplo
`POS-OPE-ADA-.YYYY.-.#####`.

Dos Custom Fields de solo lectura, ambos llamados
`restaurant_naming_series`, mostrarán la serie en `POS Opening Entry` y
`POS Closing Entry`.

Un hook `autoname` resolverá la empresa, validará sus relaciones y llamará a
`frappe.model.naming.make_autoname`. Un hook `validate` volverá a comprobar el
contexto y evitará que un valor enviado por cliente sustituya la configuración.

El cliente solo consulta y presenta el valor. La autoridad permanece en el servidor.

La migración completará únicamente campos vacíos usando la abreviatura de la empresa.
No cambiará documentos existentes ni reiniciará contadores.
