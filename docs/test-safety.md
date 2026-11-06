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
ERPNext 15.109 devuelve impuesto 38.13 y 16.53 devuelve 38.14. Las expectativas
originales permanecen como bloqueo visible hasta aceptar el contrato por version;
no modificar tasas, calculos operativos o tolerancias para ocultar esa diferencia.
