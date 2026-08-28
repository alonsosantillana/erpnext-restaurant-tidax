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
