<div align = "center">
    <img src = "https://frappecloud.com/files/pos-restaurant.webp" height = "128">
    <h2>POS Restaurant</h2>
</div>

___
> ### POS Restaurant includes the following functionalities:

1. Customized Permission Management based on ERPNext user roles.
2. Custom permissions in the POS profile assigned to rooms.
3. Management of personalized permits based on the activity of the restaurant.
4. Dynamic management of the restaurant areas.
5. Restaurant rooms, tables and production center.
6. Individual order management by table and user.
7. Process management based on Restaurant Production Center.
8. Real time based on the user's activity when the restaurant areas are modified or when the user interacts with it.
9. Compatible with Dark Theme.

___
### ERPNext Restaurant Management requires
1. Frappe 15 and ERPNext 15. The verified baseline is 15.109.0.
2. `ovenube_peru` 15.3.5 for the current TIDAX/SUNAT flow.
3. `silent_print` 0.0.1 and a configured WebApp Hardware Bridge for ticket printing.

The frontend helper used by Restaurant Manage is bundled in this app; the legacy `frappe_helper` app is not required. MFC is not a dependency.

___
### How to Install

#### Self Host:
1. Install compatible v15 versions of `ovenube_peru` and `silent_print`.
2. `bench get-app [repository-url] --branch feature/restaurant-v15-compatibility`
3. `bench setup requirements`
4. `bench --site [site.name] install-app silent_print`
5. `bench --site [site.name] install-app restaurant_management`
6. `bench build --app restaurant_management`
7. Configure Company, POS Profile, POS Opening Entry, Restaurant Company Settings, Silent Print Settings and the Hardware Bridge.

Validate first on a disposable site. See `docs/v15-baseline.md` and `docs/v15-qualification.md` for the current support matrix and evidence.

#### Receipt configuration

Configure all four series in `Restaurant Company Settings` before testing payment:

- `serie_boleta`: electronic Boleta.
- `serie_factura`: electronic Factura.
- `serie_boleta_m`: manual Boleta.
- `serie_factura_m`: manual Factura.

The payment form requires two independent selections: `Boleta`/`Factura` and `Electrónica`/`Manual`. `dinners` is only the number of diners. The currently supported identity paths require DNI for Boleta and RUC for Factura. Electronic mode invokes the `ovenube_peru` provider after local submission; Manual mode does not.

These series are resolved from `Restaurant Company Settings`, so each Company keeps independent fiscal and order numbering.

#### Reliable ticket printing

Printing is company-scoped and durable:

1. Create or review **Restaurant Print Station** for each permanent Windows cashier or kitchen workstation. The Station User must be the user logged into that browser.
2. In **Restaurant Company Settings > Reliable Ticket Printing**, map `ACCOUNT` and `INVOICE` to that station, a Print Format, a Hardware Print Type and copies. Optional `ORDER` and `KITCHEN` routes can stay disabled until physically qualified.
3. Keep WebApp Hardware Bridge running on `ws://127.0.0.1:12212` and open `/app/restaurant-print-console` in the permanent browser session. Only one live browser lease may claim a station.
4. Jobs remain `Pending` while the bridge is offline. They become `Accepted by HWB` only after a correlated acknowledgement. `Ambiguous` jobs require a person to verify the printer before retrying.
5. PDFs are rendered on demand and are not persisted in the queue. Invoice and account routes remain isolated by Company.

HWB 0.13.0 remains compatible. Test 1.0.1 separately before upgrading because it removes an old Base64 size limitation.

On Desk v16, the printer SVG appears in the active page header, or the sidebar's
standard-items area when there is no visible page header. The v15 navbar placement
remains supported. It opens the print console in a new tab, only when the server
returns a station assigned to the current user/company. Keep that console tab open
while using the station; opening it can process pending print jobs. Merely rendering
or moving the indicator does not activate a station or print.

The paired `fix-v16-printer-indicator` changes in Restaurant Management and
Silent Print preserve restaurant-indicator priority and legacy master-tab selection.
For restaurant use, update both apps in a separately authorized deployment and
hard-reload the browser to replace previously cached plain JavaScript assets.
No schema migration is needed for this UI-only correction. Offline browser evidence
and remaining real-user/HWB acceptance are recorded in
[`openspec/changes/fix-v16-printer-indicator/`](openspec/changes/fix-v16-printer-indicator/).

#### Frappe Cloud:
>Available in your hosting on FrappeCloud [here](https://frappecloud.com/marketplace/apps/restaurant_management)

___
### How to Use
> See the documentation [here](https://github.com/quantumbitcore/erpnext-restaurant/wiki)

___
### Compatibility
> Verified on Frappe/ERPNext 15.109.0. Other v15 minors require the same qualification suite; v13 and v14 are no longer part of this port target.

___
ERPNext Restaurant Management is based on [Frappe Framework](https://github.com/frappe/frappe).

___

### License
> GNU / General Public License (see [license.txt](license.txt))

> The POS Restaurant code is licensed under the GNU General Public License (v3).


## Preparacion de compatibilidad v16 (desarrollo, 2026-11-01)

Los adaptadores de APIs/campos de Frappe y ERPNext v16 se documentan en
`openspec/changes/migration-v16-compatibility/`. Se preservan las restricciones
de acceso y los contratos de lectura existentes; no se introducen cambios de
calculos contables ni tributarios.

Verificacion aislada: `python tests/test_v16_compatibility.py` (8 casos,
solo dobles; sin base de datos ni servicios externos). La revision independiente
aprobo estos escenarios con Python 3.14. La migracion del sitio y UAT funcional
son etapas separadas que coordina el expediente corporativo del upgrade.

## Navegación en Frappe v16

La pantalla **Apps** muestra **Restaurant** para usuarios internos autorizados y
abre el Workspace existente **Restaurant Management** (`/desk/restaurant-management`). El acceso
respeta los permisos actuales y las restricciones de módulo; no asigna roles.
El Dock estándar se importa de forma nativa al instalar/migrar esta app en v16.
No requiere crear Desktop Icons ni Workspace Sidebar, ni reconstruir assets.
Los iconos de Apps usan las iniciales nativas cuando no hay logo propio.

Alcance, activación puntual en desarrollo y reversión:
[OpenSpec show-apps-on-v16-desktop](openspec/changes/show-apps-on-v16-desktop/design.md).
Esta navegación exige el contrato Apps/Dock de v16; no modifica procesos de negocio.

### Icono de Apps

El acceso de **Restaurant** usa un SVG propio servido desde
`/assets/restaurant_management/images/app-icon-v1.svg`. Forma parte de una familia de símbolos funcionales con
azul petróleo, celeste y ámbar inspirados en la identidad TIDAX; no sustituye
logotipos oficiales de terceros. El archivo es vectorial, local y sin dependencias
externas. Solo cambia la imagen: conserva destino y permisos.

Diseño y reversión: [customize-v16-app-icons](openspec/changes/customize-v16-app-icons/design.md).

## Permanent POS opening compatibility (v16)

Optional, company-scoped compatibility for an older active primary POS session; default disabled. See [configuration, controls and rollback](docs/permanent-pos-opening.md).

### v16 invoice printing permission compatibility

Print and electronic-access gates use the native silent permission check (`print_logs=False`), preserving scoped authorization and queue idempotency. No migration or permission assignment is required. See [compatibility validation and rollback](openspec/changes/fix-v16-print-permission-api/design.md).
