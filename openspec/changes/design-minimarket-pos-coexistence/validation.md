# Validacion documental y matriz pendiente

## Revision

Base version-16 c96d967; rama docs/minimarket-pos-coexistence-v16.
Solo diseno OpenSpec. Revision especializada de arquitectura por subagente;
confirmada contra fuentes primarias locales. No se ejecutaron hooks, hardware,
servicios, consultas ORM ni transacciones en este trabajo.

Graphify local consultado con GRAPHIFY_QUERY_LOG_DISABLE=1: pos_series devolvio
122 nodos, salida limitada a 44. El grafo es auxiliar; hooks y codigo confirmaron
los hallazgos. No fue regenerado ni versionado.

Validaciones documentales realizadas:

- OpenSpec: openspec validate design-minimarket-pos-coexistence --strict
  --no-interactive, con Node 22.23.1 ya instalado: aprobado.
- git diff --check: aprobado para diferencias rastreadas; archivos nuevos
  revisados ademas individualmente con git diff --no-index --check.
- Solo cinco archivos Markdown nuevos bajo este expediente; sin cambios runtime.
- Matriz funcional definida, no ejecutada. Sin ORM, migracion o proveedores.
No commit/push realizado por el revisor; lo prepara el coordinador.

## Matriz futura (NO ejecutada)

Datos sinteticos autorizados: dos empresas y perfiles separados, una con settings
restaurante y otra sin ellos; perfil secundario, cajeros con permisos limitados,
aperturas/cierres de prueba, gastos en distintos estados y facturas sinteticas.
No utilizar aperturas reales ni datos fiscales de clientes para estas pruebas.

| Caso | Actor/pasos | Resultado esperado |
| --- | --- | --- |
| P01 | Cajero autorizado crea apertura/cierre no restaurante sin settings ajenos | Naming y validaciones nativas; sin restaurant_* calculados, gastos ni settings artificiales |
| P02 | Operador crea apertura/cierre restaurante con series configuradas | Series, propiedad, secuencias y gasto preservados; historicos no renombrados |
| P03 | Formulario abre sin empresa/perfil, luego selecciona empresa y perfil | No toma default de otra operacion; contexto incompleto no provoca errores de settings ajenos |
| P04 | Seleccionar apertura y manipular company/perfil discordantes por API | Rechazo explicito, sin mutaciones ni reclasificacion que evite validaciones |
| P05 | Empresa restaurante con perfil secundario/antiguo | Conserva politica documentada; no pierde series/gastos por aplicar solo pareja primaria |
| P06 | Dos operaciones en una misma empresa | Detecta que clasificacion por empresa no aisla perfiles; activacion pendiente de decision explicita |
| P07 | Doble apertura por perfil o cajero; apertura nativa antigua, futura o no enviada | Restricciones nativas conservadas; sin reutilizar o cerrar sesion ajena |
| P08 | Flag de apertura permanente off/on y perfil primario/ajeno | Solo opt-in existente permite apertura valida antigua; resto usa super sin cambiar fechas |
| P09 | Gastos borrador/enviado/sin asiento en sesion restaurante y no-restaurante | Bloqueos/calculo correctos solo en dominio configurado; no filtra gastos de otra sesion/empresa |
| P10 | Refrescar/cambiar rapidamente empresa o apertura con respuesta Ajax atrasada | Descarta respuesta; no boton, HTML ni saldos de la operacion anterior |
| P11 | Cierre ajeno con factura duplicada, borrador, perfil/cajero incorrectos o ya consolidada | Fallback nativo rechaza todos los casos; no se omite validador de super |
| P12 | Consulta de cierre por usuario sin permiso y por Guest | Servidor deniega antes de exponer datos; filtro visual no sustituye permiso |
| P13 | Consultas restaurante y ajenas bajo modalidad POS actual | Mantiene contratos v16 invoices/payments/taxes; global POS Settings y aperturas intactos |
| P14 | Consolidacion restaurante con redondeo, cambio y devolucion | Limites actuales de componentes, impuestos y origen preservados; ajena delega comportamiento nativo |
| P15 | Helpers alternan restaurante/no-restaurante y lanzan excepcion | Sin flags/estado filtrados entre llamadas; restaura valores y ausencia previos, sin commits intermedios |
| P16 | Venta no restaurante conserva politicas nativas de stock/moneda | No adopta update_stock, impuestos, almacen ni apertura permanente del restaurante |
| P17 | Ejecutar regresion restaurante completa antes/despues de guardas | Cobro, series, produccion, gastos, cierres y formatos conservados; sin emision/impresion real no autorizada |

Pruebas puras primero, con spies de super y snapshots de objetos sin guardar.
Las pruebas de sitio, concurrencia y contabilidad requieren un expediente de
implementacion y autorizacion especifica. Registrar revision Git, versiones,
actor, pasos, esperado/real y evidencia sin secretos; ninguna fila es aprobacion.
