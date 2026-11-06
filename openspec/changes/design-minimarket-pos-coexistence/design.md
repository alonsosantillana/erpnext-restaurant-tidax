# Diseno de convivencia POS (sin implementacion)

## Contexto, dependencias y alcance

Rama docs/minimarket-pos-coexistence-v16 desde version-16 c96d967; checkout limpio
antes de crear la rama. La documentacion general conserva referencias v15, pero
este expediente se dirige exclusivamente a Frappe/ERPNext version-16. No altera
la compatibilidad declarada ni expedientes historicos.

OpenSpec relacionados: add-company-pos-entry-series,
include-resto-gastos-in-pos-closing, fix-pos-closing-component-rounding,
make-restaurant-settings-multicompany, migration-v16-compatibility y
allow-permanent-pos-opening. Conservar sus contratos y explicar cualquier cambio
de alcance en el expediente de implementacion posterior.

Graphify local: consulta pos_series encontro 122 nodos (salida limitada), entre
ellos get_company_pos_series, autoname_pos_document y get_restaurant_settings.
Se confirmaron relaciones contra las fuentes. No regenerar ni versionar el grafo
por este cambio documental; no consultar sitios, proveedores o grafos externos.

## Hechos verificados y fuentes

Rutas desde la raiz del repositorio propietario. Las lineas son de la revision
actual y se deben reconfirmar antes de implementar.

| Fuente | Contrato o riesgo |
| --- | --- |
| restaurant_management/hooks.py:41-54 | Series y gastos registrados para todas las aperturas/cierres |
| restaurant_management/restaurant_management/pos_series.py:181-196,251-267 | Settings requeridos por empresa; autoname/validate globales |
| restaurant_management/public/js/pos_entry_series.js:4-19 | Consulta series al refrescar aun sin perfil; hoy falla sin settings |
| restaurant_management/restaurant_management/pos_closing_expenses.py:11-64 | Recalcula conciliacion y bloquea borradores sin guarda restaurante |
| restaurant_management/restaurant_management/expense_accounting.py:128-138 | Bloquea cierre por gastos sin asiento; tampoco discrimina perfil |
| restaurant_management/public/js/pos_closing_expenses.js:7-72 | Boton, consultas y recalculos de todos los cierres |
| restaurant_management/public/js/pos_closing_summary.js:5-11 | Reemplaza resumen de cierre; tambien requiere guarda futura |
| restaurant_management/restaurant_management/pos_closing.py:20,198-249,263-274 | Clasifica por perfil; override reimplementa validacion incluso fuera del restaurante |
| restaurant_management/restaurant_management/production.py:61-78 | Politica update_stock aplicada por empresa configurada |
| restaurant_management/restaurant_management/permanent_pos_opening.py:11-48 | Opt-in por empresa y perfil principal; resto delega a super |
| restaurant_management/restaurant_management/pos_invoice_merge.py:135-145 | Correccion de componentes restringida a perfil restaurante |
| restaurant_management/restaurant_management/doctype/table_order/table_order.py:203-225 | Moneda/impuestos restringidos a pareja empresa-perfil |
| frappe/model/naming.py:185-196 (repositorio frappe) | Un hook autoname sin nombre permite fallback a serie nativa |
| erpnext/accounts/doctype/pos_settings/pos_settings.json:29-55 (repositorio erpnext) | Modalidad en Single global, no por empresa |
| erpnext/accounts/doctype/pos_settings/pos_settings.py:78-88 | Bloqueo al cambiar modalidad con cualquier apertura activa |
| erpnext/accounts/doctype/pos_invoice/pos_invoice.py:468-471 | Sales Invoice global impide POS Invoice ordinarias |
| erpnext/accounts/doctype/pos_closing_entry/pos_closing_entry.py:72-89,106-142,268 | Cierre y consulta usan modalidad global y validaciones nativas |

## Dominio y decisiones de aislamiento

Propuesta minima para la Company separada: los ajustes de series/gastos existentes
son de alcance empresa. Una empresa con Restaurant Company Settings pertenece al
dominio restaurante para estos ajustes; una empresa sin ese registro usa ciclos
nativos. Esto mantiene el alcance historico de las empresas ya configuradas.
No crear settings de restaurante para la empresa minimarket como atajo.

NO equivale a separar restaurante y minimarket dentro de una misma empresa. Si se
requiere ese caso, debera aprobarse una identificacion explicita de perfiles y el
tratamiento de perfiles secundarios/antiguos; la pareja primaria de settings no
es un inventario completo de todos los perfiles que hoy reciben series/gastos.
No inferir dominio por nombre del usuario, empresa predeterminada, roles de cajero,
prefijo de serie, ruta de entrada ni presencia de la app instalada.

Conservar los alcances mas estrechos existentes: moneda, apertura permanente,
seleccion de facturas y componentes no se amplian a todos los perfiles de una
empresa por introducir una guarda compartida. Documentar y probar los perfiles
secundarios; no reclasificarlos silenciosamente como restaurante o minimarket.
La aprobacion posterior debe aceptar esta politica de dominio antes del codigo.

## Resolucion autoritativa y ventanas incompletas

La resolucion para guardas debe ser de lectura, sin rellenar campos ni usar los
defaults del usuario como fallback. Comparar el perfil real con su Company y, en
cierre, con la apertura seleccionada. Una contradiccion no se debe convertir en
un no-op que evite controles; fallar con validacion explicita y preservar las
validaciones nativas. No consultar datos de otra empresa para construir respuestas.

| Contexto | Tratamiento previsto |
| --- | --- |
| Sin empresa ni perfil ni apertura | No seleccionar dominio ni series; permitir completar borrador y conservar requeridos nativos |
| Perfil valido sin empresa | Leer Company del perfil para clasificar; no adoptar default del usuario ni mutar por la guarda |
| Empresa conocida sin perfil | Series pueden resolverse por empresa; gastos/cierre esperan apertura; sin cobro ni eleccion automatica de perfil |
| Cierre con apertura | Empresa/perfil autoritativos desde la apertura; comparar valores presentes del cierre |
| Empresa/perfil/apertura discordantes | Rechazo, sin reclasificacion ni correccion silenciosa |
| Empresa no configurada como restaurante | No-op de personalizaciones restaurante; ciclo y permisos nativos completos |
| Empresa restaurante con serie faltante/invalida | Mantener error y controles de propiedad; no degradar a serie nativa para eludir configuracion |

No basta invocar get_restaurant_settings(required=False) sin contexto: su resolver
puede recurrir a la empresa del usuario. No usar resolve_pos_document_company
antes de discriminar si su efecto de rellenar el documento ampliaria el alcance.

## Guardas futuras y archivos candidatos (no modificados)

1. pos_series.py autoname_pos_document/validate_pos_document_series: resolver
   contexto, discriminar dominio y retornar sin efectos fuera de el; para los
   documentos nuevos no restaurante dejar que Frappe use el autoname nativo
   POS-OPE/POS-CLO. No renombrar documentos ni reiniciar contadores existentes.
2. pos_series.get_pos_document_series y pos_entry_series.js: preservar firma y
   autenticacion/permisos; definir retorno neutro para contexto ajeno/incompleto
   y comprobarlo en cliente. No borrar valores guardados historicos. La carga
   inicial sin perfil no debe pedir settings de otra empresa ni lanzar bucles.
3. pos_closing_expenses.validate_closing_entry/validate_no_draft_expenses y
   expense_accounting.validate_expense_accounting_before_closing: guarda antes
   de consultar gastos o tocar conciliacion. Empresa ajena no modifica lineas,
   flags, resumenes ni saldos y no depende de Resto Gastos. Restaurante conserva
   sus calculos, bloqueos, redondeo y asientos completos.
4. get_closing_expense_summary y scripts pos_closing_expenses.js /
   pos_closing_summary.js: verificar permiso de la apertura antes de responder;
   acordar respuesta neutra/reconocible fuera del dominio. No mostrar boton de
   gastos ni sustituir el resumen nativo para no-restaurante. Revalidar contexto
   tras respuestas asincronas y al cambiar empresa/perfil/apertura; descartar
   respuestas atrasadas sin dejar campos de la operacion anterior.
5. RestaurantPOSClosingEntry.validate_pos_invoices: delegar a super() para
   perfiles no restaurante; mantener seleccion de facturas y contratos v16
   invoices/payments/taxes. No sustituir el resto de validaciones por un return.
6. production/permanent_pos_opening/pos_invoice_merge y moneda: revisar regresion
   sin ampliar ni reducir sus guardas existentes como efecto incidental. La
   clasificacion por empresa de update_stock exige documentar que no aisla dos
   operaciones dentro de la misma Company.

Preferir helpers internos y contratos existentes; no crear APIs, roles, DocTypes,
fixtures, patches, informes ni campos por anticipacion. Las posibles firmas,
respuestas neutras y pruebas se fijan en el expediente de implementacion, no se
publican aqui como cambios ya realizados.

## Modalidad POS y limites comerciales

Conservar POS Settings y aperturas actuales. La convivencia propuesta se disena
para la modalidad global existente; no habilita elegir Sales Invoice por empresa
mediante un settings paralelo. Si esta modalidad es POS Invoice, calificar
consolidacion, disponibilidad, libros y facturacion como tales. Stock y
contabilidad inmediatos no se deducen del mero cobro POS.

Sales Invoice por venta requiere una decision separada sobre arquitectura y
compatibilidad: cambiar el Single afecta POS y cierres de todas las empresas y
bloquea facturas POS normales del restaurante. No cerrar sesiones ajenas para
cambiarlo. Tampoco simular una venta POS fijando flags internos para saltar sus
controles. Nubefact, SUNAT y la impresion requieren sus propios escenarios y
alcance autorizado; esta convivencia no altera payloads fiscales ni reenvios.

## Flags, transacciones, datos y permisos

Las guardas no necesitan flags globales de bypass. Si una implementacion futura
usa un contexto temporal estrictamente necesario, debe guardar/restaurar valor
y existencia previa en finally, tanto en frappe.flags/frappe.local.flags como
en flags del documento; probar exito, excepcion y reentrada. Nunca desactivar
validacion, permisos, stocks, impuestos o hooks como mecanismo de aislamiento.

No introducir commits manuales ni escrituras en helpers de clasificacion.
Mantener atomicidad de documentos y reconciliaciones. No borrar columnas
restaurant_* del esquema ni normalizar documentos historicos por implicacion.
DocTypes, campos, migracion, fixtures, patches, permisos, APIs nuevas, reportes y
operaciones de servicios: no aplican en esta entrega documental.

## Aceptacion, integracion y reversion

La matriz completa esta en validation.md. Antes de implementar, crear expediente
funcional y rama propios en restaurante desde mantenimiento v16, revisar cambios
activos y obtener alcance aprobado. Primero calificar guardas/fallback nativo;
despues activar pruebas comerciales del minimarket. Navegacion sola no sustituye
esa dependencia ni autoriza usar formularios para crear operaciones.

No aplicar al sitio desde esta tarea. Para futura activacion, volver a verificar
perfiles, settings, sesiones, modo global y documentos custom sin publicar datos
personales. Escenarios con escrituras/integraciones necesitan autorizacion
especifica. No presentar mocks/sintaxis como aceptacion comercial.

Reversion actual: revertir solo el commit documental cuando exista, sin datos
creados. Reversion futura: volver al commit de codigo revisado con la operacion
coordinada; ello puede reintroducir bloqueo de aperturas de empresas ajenas.
Evaluar documentos nuevos/contadores y sesiones activas antes de revertir; no
borrar ni renombrar transacciones, ni restaurar una base compartida sin analisis
y autorizacion. Migracion inversa solo si se aprueba un cambio de esquema aparte.
