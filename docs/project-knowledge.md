# Estado de OpenSpec y Graphify

Revisión: 2026-11-13 (America/Lima). App: restaurant_management, desarrollo.
Auditoría inicial del código instalado: `8138a20`, rama documental
`docs/refresh-openspec-graphify-20261113`, commit ccdf75a. Esta copia se adapta a
la principal version-16 desde 037c8a1. No se modificó lógica funcional.

## Alcance y procedencia

El checkout instalado estaba limpio y en detached HEAD en 8138a20. La referencia
local de mantenimiento version-16 estaba en 037c8a1; la cotización nativa de
carrito posterior pertenece a una rama dedicada. Se creó la rama documental desde
el checkout instalado para describirlo sin integrar, sustituir o desplegar fuentes.
La auditoría inicial no actualizó referencias remotas; la integración documental
posterior sí actualiza la referencia de version-16 antes de publicar.

OpenSpec conserva decisiones y evidencia; Graphify orienta el análisis estático.
Ninguno acredita por sí solo datos correctos, permisos efectivos, homologación
de PedidosYa, canales activados ni aceptación transaccional en v16.

## Integración autorizada en version-16

El usuario solicitó incorporar la documentación y publicarla. Se aplicó solo el
commit documental ccdf75a desde la base de mantenimiento 037c8a1, sin fusionar sus
ancestros funcionales 1d80944/8138a20. La cotización de carrito y sus tests no se
incorporan. Las referencias candidatas son externas e inmutables, y sus requisitos
no se incluyen como capacidad consolidada de la principal.

La rama instalada y su grafo local permanecen sin cambios. La validación de
mantenimiento se hace en un worktree aislado: no es despliegue, migración ni
certificación funcional. El hash publicado y el resultado del push se comunican
separadamente tras comprobar el remoto.

## OpenSpec

- Auditoría original instalada: 54 de 56 expedientes pasaban; tras corregirlos,
  56 expedientes y 8 capacidades consolidadas validaron (64 elementos).
- version-16 documental: 55 expedientes y 7 capacidades consolidadas pasan
  (62 elementos, cero fallos); se excluyen el expediente y la spec del carrito candidato.
- account-resto-gastos-on-submit: se normalizaron encabezados/deltas y se
  explicitaron escenarios ya definidos por el diseño y presentes en el código.
- make-resto-gastos-multicompany: se recuperaron los deltas ausentes desde su
  propuesta/diseño y se contrastaron contra controlador, series y reporte.
- [Base consolidada](../openspec/specs/README.md): gastos multiempresa/contabilidad,
  indicador/permisos de impresión, compatibilidad v16 y
  transporte/autenticación de callbacks PedidosYa. No es consolidación exhaustiva.
- Se actualizaron contexto v16, índice y README. La antigua exclusión contable
  del primer cambio de gastos no anula el cambio contable posterior.
- No se archivó ningún expediente ni se convirtió una tarea pendiente en una
  prueba aprobada por el mero hecho de que la especificación valide.

### Reconciliación de evidencia

El operador informó previamente que la ticketera imprimió y que el indicador
aparece en el sitio de desarrollo. Se registró como confirmación acotada del
operador, no como nueva prueba automática, aceptación de todas las estaciones o
confirmación de que los dos trabajos pendientes quedaron resueltos.

La entrega de esta conversación confirmó el merge/push autorizado de los commits
de indicador 430dd62 y 2063fc4. La ascendencia local confirma el primero en la
fuente auditada. La publicación posterior de la corrección de cola PedidosYa
también fue reconciliada con la conversación y los ancestros ba59719/cc765f9.
No se realizó un nuevo push ni se consultó otro servidor para hacer esta revisión.

Los resultados transaccionales antiguos de gastos se preservan como históricos.
No se repitieron en v16 y no acreditan pruebas completas por compañía.
Los límites de cotización nativa, permisos heredados y puesta en servicio se
conservan en sus expedientes. La homologación oficial de PedidosYa no se da por
realizada por contar con pruebas contra receptores simulados.

## Graphify — checkout instalado, no grafo de mantenimiento

- Anterior: 2026-10-26, commit 7fe18ef6, 2427 nodos y 4451 relaciones.
- Regenerado: 2026-11-13, 2711 nodos, 4954 relaciones y 258 comunidades.
- AST local sobre 361 archivos clasificados como código, con dos procesos.
  No hubo análisis de documentos/imágenes, llamadas LLM, BD viva ni integración externa.
- Se regeneraron grafo, manifiesto, análisis, informe y HTML locales. Los nombres
  de comunidades se validan/reutilizan localmente o derivan del nodo hub.
- El grafo ya incluye quote_cart y los cambios recientes de v16 y callbacks.
  Sus inferencias AST siguen siendo hipótesis que hay que contrastar con código.
- Advertencia conservada: 75 archivos sin nodos, principalmente JSON y módulos
  vacíos; no se certifica cobertura de relaciones dinámicas de DocTypes/fixtures/hooks.
- Respaldo recuperable previo:
  `graphify-out/pre-refresh-20261113-aPtfv3/`. Graphify conserva además sus propias
  copias fechadas. No se borró ningún grafo histórico.
- Artefactos generados ignorados por Git, no versionados ni publicados. El hash
  de construcción se comprueba en graph.json y GRAPH_REPORT.md después del commit
  documental local ccdf75a; los documentos no forman parte de la extracción
  code-only. No es el grafo de version-16, cuya fuente ejecutable no incluye el carrito.

Procedimiento y límites: [Graphify](graphify.md).

## Verificación reproducible

Desde la raíz de esta app, usando herramientas ya instaladas:

```bash
OPENSPEC_TELEMETRY=0 /home/erpnext/.nvm/versions/node/v22.23.1/bin/node /home/erpnext/.local/bin/openspec validate --all --strict --no-interactive
git diff --check
```

La validación documental no ejecuta pruebas Frappe ni abre sitios. La regeneración
del grafo requiere autorización, como describe la guía enlazada; no instalar
herramientas, activar proveedores ni modificar configuración MCP como paso implícito.

Comprobaciones de la revisión instalada original: 64 elementos OpenSpec válidos,
87 enlaces relativos sin rutas rotas, 8 requisitos consolidados equivalentes y
presencia de cotización, indicador y callbacks en el grafo con respaldo anterior.
El commit ccdf75a no cambió fuentes ejecutables respecto de 8138a20.

Comprobación de esta integración de mantenimiento: 62 elementos OpenSpec válidos,
siete capacidades consolidadas, 83 enlaces locales sin rutas rotas y cero diferencias en
fuentes ejecutables, tests, tools o empaquetado respecto de 037c8a1. No se versionan
artefactos ignorados de Graphify ni se incorporan commits funcionales del carrito.

## Inventario de expedientes

Casillas leídas de tasks.md en la principal candidata, no una clasificación de aceptación funcional.
Cero pendientes no equivale a despliegue; algunas casillas pendientes son
exclusiones expresas o aceptación externa. Los expedientes v15 son históricos.
No se archivan ni se ejecutan automáticamente estas tareas.

| Expediente | Marcadas | Pendientes |
| --- | ---: | ---: |
| [account-resto-gastos-on-submit](../openspec/changes/account-resto-gastos-on-submit/tasks.md) | 9 | 1 |
| [add-company-pos-entry-series](../openspec/changes/add-company-pos-entry-series/tasks.md) | 9 | 0 |
| [add-consolidated-tip-settlement](../openspec/changes/add-consolidated-tip-settlement/tasks.md) | 10 | 1 |
| [add-native-table-service](../openspec/changes/add-native-table-service/tasks.md) | 4 | 0 |
| [add-pre-account-table-state](../openspec/changes/add-pre-account-table-state/tasks.md) | 17 | 0 |
| [add-readonly-order-quote-r9e2](../openspec/changes/add-readonly-order-quote-r9e2/tasks.md) | 7 | 2 |
| [add-reliable-ticket-printing](../openspec/changes/add-reliable-ticket-printing/tasks.md) | 17 | 3 |
| [add-restaurant-delivery](../openspec/changes/add-restaurant-delivery/tasks.md) | 39 | 10 |
| [add-restaurant-operational-roles](../openspec/changes/add-restaurant-operational-roles/tasks.md) | 7 | 0 |
| [add-restaurant-table-reservations](../openspec/changes/add-restaurant-table-reservations/tasks.md) | 13 | 0 |
| [add-restaurant-tips](../openspec/changes/add-restaurant-tips/tasks.md) | 9 | 1 |
| [allow-permanent-pos-opening](../openspec/changes/allow-permanent-pos-opening/tasks.md) | 6 | 0 |
| [compact-pos-payment-methods](../openspec/changes/compact-pos-payment-methods/tasks.md) | 18 | 0 |
| [confirm-restaurant-production](../openspec/changes/confirm-restaurant-production/tasks.md) | 6 | 1 |
| [customize-v16-app-icons](../openspec/changes/customize-v16-app-icons/tasks.md) | 8 | 0 |
| [default-selectable-guest-count](../openspec/changes/default-selectable-guest-count/tasks.md) | 12 | 0 |
| [design-waiter-mobile-app](../openspec/changes/design-waiter-mobile-app/tasks.md) | 2 | 29 |
| [diagnose-restaurant-pos-currency](../openspec/changes/diagnose-restaurant-pos-currency/tasks.md) | 6 | 0 |
| [differentiate-production-action-colors](../openspec/changes/differentiate-production-action-colors/tasks.md) | 6 | 0 |
| [expose-mobile-order-management](../openspec/changes/expose-mobile-order-management/tasks.md) | 5 | 0 |
| [expose-mobile-pre-account-state](../openspec/changes/expose-mobile-pre-account-state/tasks.md) | 6 | 0 |
| [expose-ready-dish-count](../openspec/changes/expose-ready-dish-count/tasks.md) | 4 | 0 |
| [filter-waiter-reports-by-pos-session](../openspec/changes/filter-waiter-reports-by-pos-session/tasks.md) | 8 | 0 |
| [fix-client-script-name-migration](../openspec/changes/fix-client-script-name-migration/tasks.md) | 9 | 1 |
| [fix-company-settings-migration-series](../openspec/changes/fix-company-settings-migration-series/tasks.md) | 7 | 1 |
| [fix-kitchen-pos-profile-permissions](../openspec/changes/fix-kitchen-pos-profile-permissions/tasks.md) | 7 | 1 |
| [fix-mobile-offpremise-pos-room-authorization](../openspec/changes/fix-mobile-offpremise-pos-room-authorization/tasks.md) | 4 | 1 |
| [fix-pedidosya-callback-queue](../openspec/changes/fix-pedidosya-callback-queue/tasks.md) | 13 | 0 |
| [fix-pedidosya-jwt-auth-hook](../openspec/changes/fix-pedidosya-jwt-auth-hook/tasks.md) | 14 | 0 |
| [fix-pos-closing-component-rounding](../openspec/changes/fix-pos-closing-component-rounding/tasks.md) | 9 | 1 |
| [fix-pos-preview-configured-payment](../openspec/changes/fix-pos-preview-configured-payment/tasks.md) | 9 | 2 |
| [fix-print-station-client-compatibility](../openspec/changes/fix-print-station-client-compatibility/tasks.md) | 6 | 1 |
| [fix-v16-print-permission-api](../openspec/changes/fix-v16-print-permission-api/tasks.md) | 7 | 0 |
| [fix-v16-printer-indicator](../openspec/changes/fix-v16-printer-indicator/tasks.md) | 9 | 1 |
| [implement-resto-tix-mobile-api](../openspec/changes/implement-resto-tix-mobile-api/tasks.md) | 20 | 8 |
| [improve-80mm-invoice-printing](../openspec/changes/improve-80mm-invoice-printing/tasks.md) | 14 | 1 |
| [improve-mobile-order-price-errors](../openspec/changes/improve-mobile-order-price-errors/tasks.md) | 14 | 0 |
| [include-resto-gastos-in-pos-closing](../openspec/changes/include-resto-gastos-in-pos-closing/tasks.md) | 12 | 2 |
| [inherit-mobile-role-actions](../openspec/changes/inherit-mobile-role-actions/tasks.md) | 11 | 3 |
| [integrate-pedidosya-pos](../openspec/changes/integrate-pedidosya-pos/tasks.md) | 23 | 1 |
| [keep-order-actions-visible](../openspec/changes/keep-order-actions-visible/tasks.md) | 5 | 0 |
| [make-electronic-pos-submission-recoverable](../openspec/changes/make-electronic-pos-submission-recoverable/tasks.md) | 10 | 0 |
| [make-restaurant-settings-multicompany](../openspec/changes/make-restaurant-settings-multicompany/tasks.md) | 18 | 3 |
| [make-resto-gastos-multicompany](../openspec/changes/make-resto-gastos-multicompany/tasks.md) | 12 | 1 |
| [manage-restaurant-tip-corrections](../openspec/changes/manage-restaurant-tip-corrections/tasks.md) | 19 | 4 |
| [migration-v16-compatibility](../openspec/changes/migration-v16-compatibility/tasks.md) | 5 | 1 |
| [pilot-mcp-read-boundary-v16](../openspec/changes/pilot-mcp-read-boundary-v16/tasks.md) | 9 | 3 |
| [port-restaurant-management-to-v15](../openspec/changes/port-restaurant-management-to-v15/tasks.md) | 70 | 54 |
| [prepare-mcp-v16-scoped-integration](../openspec/changes/prepare-mcp-v16-scoped-integration/tasks.md) | 12 | 1 |
| [preserve-pos-consolidation-totals](../openspec/changes/preserve-pos-consolidation-totals/tasks.md) | 9 | 0 |
| [refresh-pedidosya-callback-token](../openspec/changes/refresh-pedidosya-callback-token/tasks.md) | 9 | 0 |
| [retire-legacy-restaurant-settings](../openspec/changes/retire-legacy-restaurant-settings/tasks.md) | 8 | 0 |
| [show-apps-on-v16-desktop](../openspec/changes/show-apps-on-v16-desktop/tasks.md) | 9 | 0 |
| [show-completed-pickups-on-board](../openspec/changes/show-completed-pickups-on-board/tasks.md) | 10 | 2 |
| [support-configured-quote-service-charges](../openspec/changes/support-configured-quote-service-charges/tasks.md) | 7 | 0 |


## Límites operativos y siguientes pasos

No se ejecutó bench migrate/restart/update, no hubo cambios de configuración,
datos, scheduler, colas o roles, ni conexión a producción, HWB o proveedores.
No se ejecutaron suites transaccionales ni se enviaron trabajos de impresión.
La integración documental fue autorizada expresamente; no autoriza incorporar
la rama de cotizaciones a mantenimiento. La publicación se verifica e informa
separadamente en la entrega. Se conservan la rama documental instalada original
y su grafo, sin cambiarlos de revisión ni sustituir sus fuentes.

Los expedientes restantes pueden consolidarse por capacidad tras revisar sus
solapamientos y evidencia; no aplicar todos los deltas históricos ciegamente.
Las pruebas manuales, permisos/estaciones adicionales y homologación externa
conservan sus autorizaciones y condiciones originales. Para revertir solo esta
documentación, revertir su commit; para el grafo, recuperar el respaldo indicado,
sin tocar datos o fuentes operativas.
