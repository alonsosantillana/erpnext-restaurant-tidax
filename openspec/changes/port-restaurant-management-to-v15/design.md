## Context

`restaurant_management` es un fork 1.7.7 de `alphabit-technology/erpnext-restaurant` con personalizaciones TIDAX agregadas sobre cocina, gastos, cambio de mozo, reportes y facturacion electronica peruana. El upstream actual 1.8.6 declara soporte v15 e integra Frappe Helper, pero tambien contiene comportamientos obsoletos y no incluye las personalizaciones locales; por ello no es seguro reemplazar el arbol local ni fusionarlo sin seleccion.

El bench objetivo usa Frappe/ERPNext 15.109.0. La app esta presente en `apps/`, pero no instalada en `v15.local`. El analisis detecto bloqueos de runtime (`frappe.jshtml`, `frappeHelper`, `Desk Form`, `POS Settings.is_online`), dependencias no declaradas, endpoints sin autorizacion suficiente, SQL interpolado, commits manuales, cambios directos de `docstatus`/`owner`, estados de cocina destructivos, reportes sin aislamiento por compania y ausencia de pruebas reales.

Interesados principales: administradores ERPNext, cajeros, mozos, cocineros, responsables de restaurante, contabilidad y responsables de facturacion electronica/SUNAT.

Restricciones:

- No modificar `frappe` ni `erpnext`.
- Preservar el comportamiento TIDAX validado; los cambios tributarios requieren aprobacion independiente.
- No probar inicialmente sobre un sitio operativo.
- Cualquier patch debe ser idempotente y reversible mediante respaldo o patch compensatorio.
- `ovenube_peru`, `silent_print` y WebApp Hardware Bridge deben tratarse como integraciones explicitas, no como globals accidentales; la funcionalidad que dependia de MFC sera propia de esta app.

## Goals / Non-Goals

**Goals:**

- Instalar, migrar y cargar la app en Frappe/ERPNext v15 sin dependencias implicitas ni errores de frontend.
- Mantener los flujos actuales de restaurante y personalizaciones TIDAX que superen la validacion funcional.
- Aplicar permisos en servidor, aislamiento por compania y consultas parametrizadas.
- Hacer atomicos y auditables los cambios de ordenes, cocina, pagos y facturas.
- Configurar series, impresion e integracion electronica sin usuarios ni valores operativos hardcodeados.
- Incorporar pruebas automatizadas y una matriz end-to-end reproducible.

**Non-Goals:**

- Adoptar todas las funcionalidades nuevas del upstream 1.8.6.
- Reescribir el frontend con otro framework.
- Cambiar reglas SUNAT o payloads de `ovenube_peru` sin especificacion tributaria adicional.
- Corregir codigo de apps externas dentro de este cambio.
- Ejecutar despliegue productivo, migracion o cambios de datos sin una autorizacion posterior.

## Decisions

### 1. Port selectivo basado en capacidades

Se comparara cada componente local con upstream 1.8.6 y ERPNext v15. Solo se incorporaran piezas necesarias para compatibilidad o seguridad. Las personalizaciones locales se conservaran como deltas identificables.

Alternativas consideradas:

- **Reemplazar por upstream:** descartado porque eliminaria reportes, DocTypes y logica TIDAX, y heredaria defectos aun presentes en upstream.
- **Mantener 1.7.7 y agregar parches puntuales:** insuficiente porque faltan capas completas del helper y contratos de dependencias.

### 2. Integrar el helper minimo dentro de la app

La app sera autocontenida para `frappe.jshtml`, `frappeHelper`, `DeskForm`, `DeskModal` y controles requeridos. Se tomara como referencia el helper integrado del upstream, revisando su compatibilidad, licencia y superficie antes de portar archivos. Los assets se registraran explicitamente en hooks y se eliminaran referencias muertas.

Se prefiere integrar el subconjunto minimo frente a reinstalar la antigua app `frappe_helper`, porque el upstream ya retiro esa dependencia separada y el sitio objetivo no la contiene.

### 3. Dependencias declaradas y capacidades opcionales

- `frappe` y `erpnext` v15 seran dependencias requeridas.
- `ovenube_peru` sera requerida mientras la facturacion electronica TIDAX permanezca acoplada al flujo de pago.
- `silent_print` y WebApp Hardware Bridge seran dependencias operativas requeridas para imprimir comandas, boletas y facturas. Una falla de impresion no revertira ni corrompera una venta ya persistida y dejara una accion reintentable.
- Las referencias a DocTypes MFC se reemplazaran por DocTypes propios de `restaurant_management`; la app no dependera de MFC.
- `posawesome` y `Work Station` se retiraran si se confirma que son codigo muerto; de lo contrario se documentaran y protegeran como dependencia explicita.

La deteccion de apps se realizara en servidor. El frontend recibira capacidades habilitadas y no inferira dependencias por globals.

### 4. Compatibilidad de inicializacion POS v15

La pagina dejara de consultar `POS Settings.is_online`. La inicializacion validara en servidor: usuario autenticado, compania por defecto, perfil POS accesible, apertura POS requerida y dependencias habilitadas. El `<body>` global no se ocultara; los errores se mostraran dentro de la pagina y siempre liberaran cualquier estado de carga.

Las llamadas a metodos ERPNext v15 se centralizaran en un adaptador pequeno para reducir el costo de futuras actualizaciones.

### 5. Seguridad en servidor como fuente de verdad

Cada metodo whitelisted tendra:

- autenticacion explicita; no se permitiran invitados para configuracion o datos del POS;
- validacion de rol y permisos sobre el DocType/documento;
- validacion de compania, perfil POS, sala y propiedad cuando corresponda;
- tipos y formatos de entrada validados;
- consultas ORM o SQL parametrizado;
- respuestas minimas sin campos tributarios o personales innecesarios.

Los controles visuales solo mejoraran UX y no sustituiran permisos. Los valores mostrados en HTML se insertaran con APIs de texto o escape estandar, nunca por concatenacion de datos no confiables.

### 6. Estado y transacciones de ordenes

Se definira una maquina de estados unica para `Order Entry Item`. Las transiciones permitidas se validaran en servidor y registraran usuario y tiempo cuando aplique. El scheduler no sobrescribira estados finales; cualquier cierre automatico operara solo sobre estados expresamente vencidos y conservara trazabilidad.

`Table Order` conservara `is_submittable` y se finalizara mediante `submit()`; cualquier anulacion usara `cancel()` cuando corresponda. No se escribira `docstatus` directamente.

Cada accion de negocio se ejecutara dentro de la transaccion de la solicitud. Se eliminaran `frappe.db.commit()` internos salvo una justificacion documentada. Una excepcion revertira orden, items, pago y vinculos creados en esa accion.

Para concurrencia sobre mesa u orden se usaran validaciones de ultima modificacion y, cuando sea necesario, bloqueo de fila acotado. Los eventos realtime se publicaran despues de persistir correctamente; los clientes recargaran el estado autoritativo en lugar de aplicar cambios ciegos.

### 7. Facturacion y cumplimiento TIDAX/SUNAT

La creacion de `POS Invoice` se separara en:

1. validacion de usuario, cliente, identificacion, items, stock y pagos;
2. seleccion explicita de Boleta o Factura y resolucion de configuracion tributaria por compania y contexto operativo;
3. construccion mediante APIs de ERPNext;
4. validacion y `submit()` de la factura;
5. vinculacion atomica con `Table Order`;
6. envio electronico e impresion como operaciones controladas posteriores.

`dinners` representara exclusivamente la cantidad de comensales. El tipo de comprobante se guardara en un campo explicito Boleta/Factura, independiente de `dinners`; DNI o RUC podran sugerir una opcion, pero nunca se inferira el comprobante por la cantidad de comensales.

Series de factura/boleta, incluidas temporalmente las variantes `_m` hasta confirmar su significado, formatos y modos de pago se leeran de configuracion validada por compania y contexto operativo. No se asignara `owner`; Frappe conservara al usuario real. Se probaran DNI, RUC, otros documentos autorizados, descuentos por linea, descuento global, gratuidad parcial/total, impuestos incluidos, multiples medios de pago y errores de SUNAT.

Si el envio electronico falla despues de crear la factura, se registrara un estado recuperable y reintentable sin duplicar el comprobante. Logs y errores no contendran credenciales ni datos personales completos.

### 8. Metadatos, fixtures y migracion

Los Custom Fields y Client Scripts propios se versionaran con fixtures filtrados o definiciones estandar. `after_migrate` no ejecutara borrados directos. Cualquier normalizacion de campos duplicados, referencias MFC o datos historicos se implementara como patch idempotente que primero inspeccione el estado.

Antes de escribir patches se levantara un inventario de datos sobre una copia: estados, ordenes abiertas, items huerfanos, `docstatus`, dependencias, series y enlaces a `POS Invoice`.

### 9. Reportes y rendimiento

Todos los reportes aplicaran `company`, rango de fechas, `docstatus` y permisos. Se corregiran bordes de calendario y se evitara `SELECT *`. SQL agregado se parametrizara y se revisara con volumen representativo. Los endpoints de items y cocina tendran limites y filtros indexables.

### 10. Impresion mediante hardware bridge

`silent_print` sera la interfaz de la app con WebApp Hardware Bridge y la tiketera. La configuracion resolvera impresora, formato y clase de documento para comandas, boletas y facturas. La impresion se solicitara solo despues de persistir la operacion correspondiente.

El resultado de impresion quedara separado del estado comercial: una falla conservara la orden o factura valida, mostrara un error accionable y permitira reintentar sin duplicar la venta ni el comprobante.

### 11. Estrategia de pruebas

La implementacion usara:

- pruebas unitarias para transiciones, permisos, validacion tributaria y calculos;
- pruebas Frappe de integracion para documentos y rollback;
- pruebas de API para usuarios y companias distintas;
- validacion de sintaxis, hooks, JSON, fixtures y OpenSpec;
- instalacion limpia y migracion desde una copia 1.7.7;
- prueba manual end-to-end en navegador con consola y logs supervisados.

Matriz minima:

| Area | Casos |
|---|---|
| Instalacion | instalacion limpia, migrate repetido, assets, dependencias ausentes/presentes |
| Permisos | administrador, cajero, mozo, cocinero, acceso cruzado por sala/compania |
| Orden | crear, editar, enviar, dividir, transferir, cambiar mozo, eliminar permitido/bloqueado |
| Cocina | filtros cocina/bar, concurrencia, completar, estados finales, realtime |
| Factura | boleta, factura, DNI, RUC, descuentos, gratuidad, pagos multiples, stock insuficiente |
| Integraciones | SUNAT exitoso/fallido/reintento, impresion presente/ausente |
| Reportes | companias separadas, diciembre, cancelados, rangos vacios y volumen representativo |

## Risks / Trade-offs

- **[Regresion TIDAX por diferencias con upstream]** -> Port por componente, diffs pequenos y pruebas de factura/comanda antes de integrar cada fase.
- **[Corrupcion de ordenes historicas]** -> Inventario previo, patches idempotentes, respaldo y prueba sobre copia restaurada.
- **[Cambio de totales o impuestos]** -> Comparacion de fixtures de factura antes/despues y aprobacion tributaria para cada caso.
- **[Condiciones de carrera en horas pico]** -> Pruebas concurrentes, transacciones cortas y bloqueo solo donde sea necesario.
- **[Dependencias externas no disponibles]** -> Validacion al iniciar la operacion afectada, errores claros y reintento de impresion sin alterar la venta persistida.
- **[Port del helper aumenta superficie frontend]** -> Incorporar solo archivos usados, fijar su procedencia/licencia y cubrir carga con pruebas.
- **[Mayor tiempo de entrega por amplitud]** -> Implementacion en fases P0-P4, cada una desplegable y revisable por separado.
- **[Eliminacion de commits manuales cambia tiempos realtime]** -> Publicar eventos solo al finalizar con exito y recargar estado autoritativo.

## Migration Plan

1. Crear respaldo y clon aislado del sitio representativo.
2. Inventariar apps, versiones, Custom Fields, Client Scripts, DocTypes externos y datos historicos.
3. Implementar y validar primero runtime/dependencias sin migrar datos funcionales.
4. Aplicar seguridad y permisos; ejecutar pruebas negativas.
5. Migrar ciclo de ordenes y estados con patch idempotente si se requiere.
6. Migrar facturacion/configuracion TIDAX y ejecutar comparacion tributaria.
7. Corregir reportes y completar la matriz end-to-end.
8. Ejecutar instalacion limpia y upgrade desde 1.7.7 en sitios desechables.
9. Preparar ventana de despliegue, respaldo, checklist y observabilidad.
10. Desplegar solo con aprobacion; verificar smoke tests antes de abrir operaciones.

### Rollback

- Revertir a la rama/commit previo y restaurar el respaldo si un patch altero datos.
- Cada patch de metadatos debera documentar su compensacion o restauracion.
- No cancelar ni eliminar facturas generadas durante pruebas reales sin procedimiento contable autorizado.
- Las integraciones externas se podran deshabilitar por configuracion sin impedir consultar ordenes existentes.

## Open Questions

- ¿Que estados historicos y volumen de ordenes deben normalizarse durante el upgrade?
- ¿Que versiones exactas de `ovenube_peru` y ERPNext v15 formaran la matriz soportada?

## Confirmed Decisions

- La funcionalidad de produccion que usaba MFC se conservara mediante DocTypes propios de `restaurant_management`.
- `dinners` se usara solo para la cantidad de comensales; Boleta/Factura tendra seleccion explicita y configurada.
- Las variantes de serie `_m` corresponden a emision Manual; el modo Electronica/Manual sera una seleccion separada del tipo de comprobante.
- `silent_print` y WebApp Hardware Bridge se conservaran para comandas, boletas y facturas, con fallos reintentables que no corrompan la venta.
- `Table Order` seguira siendo submittable y se finalizara con la API documental de Frappe.
- Se autoriza implementar y validar en un sitio v15 desechable antes de cualquier despliegue operativo.
