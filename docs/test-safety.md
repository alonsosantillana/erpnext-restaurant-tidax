# Seguridad de las pruebas

No ejecute `bench --site v15.local run-tests` ni pruebas de Frappe/ERPNext en
ningún sitio que contenga configuración o datos operativos.

El inicializador global de pruebas de ERPNext elimina y confirma datos maestros
para construir su escenario de prueba. Entre esos datos se encuentran todos los
registros de `Item Price`; por ello, ejecutar la suite sobre un sitio operativo
puede dejar los productos del POS con precio cero.

## Procedimiento obligatorio

1. Cree o restaure un sitio desechable dedicado a pruebas.
2. Instale en él las aplicaciones y fixtures necesarios.
3. Autorice expresamente las pruebas destructivas sólo en ese sitio:

   ```bash
   bench --site restaurant-test.local set-config restaurant_allow_destructive_tests true
   ```

4. Ejecute la suite mediante el protector del repositorio:

   ```bash
   apps/restaurant_management/scripts/run-tests-safe.sh restaurant-test.local
   ```

El protector rechaza cualquier sitio que no tenga
`restaurant_allow_destructive_tests: true` en su `site_config.json`.

No establezca esa opción en `v15.local` ni en un sitio de producción.

## Fixtures offline v15/v16

`restaurant_management.restaurant_management.test_order_quote` puede ejecutarse
con `python -B -m unittest` y las dependencias ya disponibles, fuera de cualquier
inicializacion de sitio. Usa documentos sinteticos con el constructor POSInvoice,
el helper de precios y el motor de impuestos reales; bloquea init/connect,
escrituras, validacion POS, FX y red. No usar `bench run-tests` para esta prueba.
Seleccionar explicitamente los checkouts revisados mediante PYTHONPATH para
las pruebas emparejadas de TIX; no instalar paquetes ni cambiar el bench.

El fixture restaura atributos del contexto local en ejecucion serial, incluso
tras fallos de setup. No garantiza identidad del diccionario interno ni
sincronizacion entre contextos concurrentes.

La adaptacion se especifica en
[fix-v15-v16-quote-test-fixtures](../openspec/changes/fix-v15-v16-quote-test-fixtures/design.md).
La validacion sintetica no certifica un sitio ni una localizacion tributaria.
Las versiones inspeccionadas difieren en redondeo inclusivo: para total 250,
ERPNext 15.109 devuelve impuesto 38.13 y 16.53 devuelve 38.14. El usuario acepto
expectativas exactas por version: 38.13 para v15 y 38.14 para v16, sin cambiar
el total 250. El helper solo de pruebas usa valores fijos independientes del
resultado calculado y rechaza majors desconocidos. No se modificaron tasas,
calculos operativos, precisiones ni tolerancias; las 55 pruebas enfocadas
nativas/emparejadas/aprobacion pasan en ambas matrices inspeccionadas.
Evidencia y limites:
[accept-native-inclusive-tax-test-matrix](../openspec/changes/accept-native-inclusive-tax-test-matrix/tasks.md).

## Verificacion de la pareja de fuentes

La rama `docs/quote-paired-source-verification` parte de `4d01d2e`
(`fix/quote-native-tax-expectations`), con las correcciones anteriores ya
incluidas. Este seguimiento agrega solo documentacion: no modifica el motor,
impuestos ni fixtures. Se verifico junto a TIX
`fix/mcp-release-cli-paired-gates`, basado en `018d19e`, en worktrees persistentes
aislados; no se sustituyo el checkout instalado de ninguna app.

Antes de probar, fijar ambos roots en `PYTHONPATH` y comprobar las rutas reales
de `tix.__file__` y `test_order_quote.__file__`. El checkout instalado puede no
contener `isolated_local` ni `expected_inclusive_tax`: no asumir que una rama
complementaria pendiente ya esta aplicada al sitio.

Con Python 3.14.3, Frappe 16.55.2 y ERPNext 16.53.0 pasaron 36 pruebas nativas,
9 emparejadas de TIX (incluida limpieza ante fallo parcial de setup) y 5 de
diagnostico con datos sinteticos. Son 50 pruebas distintas; las repeticiones no
se suman. Esta ejecucion no revalida v15, no certifica un sitio ni amplifica los
rangos publicados del MCP. La evidencia TIX esta en
`mcp_server/docs/release-cli-paired-validation.md` de la rama indicada.

Integrar las correcciones de `4d01d2e` en la linea de mantenimiento requiere una
operacion Git aprobada por separado; ni esta documentacion ni los tests offline
equivalen a merge, despliegue o migracion. No se necesita una nueva correccion
funcional de Restaurant para esta pareja, ni cambios en datos de negocio.
