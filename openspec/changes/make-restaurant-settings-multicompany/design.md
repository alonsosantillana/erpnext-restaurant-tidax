## Architecture

### Configuración por empresa

`Restaurant Company Settings` será un DocType normal, nombrado por `company`, con los
campos funcionales del `Single` actual. `company` será obligatorio y único.

El módulo `company_settings.py` será la única entrada para obtener configuración:

1. empresa del documento (`Table Order` o `Restaurant Fulfillment`);
2. empresa del POS Profile;
3. empresa explícita;
4. empresa predeterminada del usuario.

Cuando no exista un registro por empresa solo se permitirá usar el `Single` legado para
la empresa marcada durante la migración. Para otras empresas se mostrará un error de
configuración.

### Contexto POS

El POS Profile se resolverá por Company y usuario. El campo `pos_profile` de la
configuración se tratará como perfil predeterminado opcional, validando que pertenezca
a la misma empresa. La empresa persistida en la orden será autoritativa después de
crear el documento.

### Objetos del restaurante

`Restaurant Object.company` será obligatorio para nuevos registros. Un ambiente toma
la empresa activa; una mesa o centro de producción hereda la empresa de su ambiente.
El servidor rechazará relaciones entre empresas.

Todas las consultas operativas incorporarán `company`. Las actualizaciones realtime
conservarán los canales actuales por objeto, cuyos nombres ya son específicos, y los
eventos globales incluirán `company` para que el cliente descarte otros contextos.

### Series e impresión

Las cuatro series de boleta/factura y los formatos se resolverán desde la empresa de
la orden. No se copiarán valores a empresas adicionales porque eso podría duplicar
series fiscales. El enrutamiento a impresora física no se moverá a este DocType.

## Migration

El patch:

1. identifica la empresa global predeterminada o la única empresa del sitio;
2. crea `Restaurant Company Settings` si no existe;
3. copia campos simples y filas de `Restaurant Exceptions`;
4. asigna esa empresa a objetos sin `company`;
5. guarda la empresa migrada como referencia de fallback legado.

Es idempotente y no modifica órdenes, fulfillments ni facturas históricas.

## Permissions and Security

- La configuración conserva los roles actuales y aplica permisos de `Company`.
- Las APIs derivan la empresa de documentos persistidos cuando existen.
- El cliente no puede seleccionar arbitrariamente otra empresa para facturar una orden.
- Las consultas de mesas y producción filtran por empresa además de los permisos
  existentes por sala y rol.

## Rollback

- Revertir código conserva `Restaurant Company Settings` y `Restaurant Object.company`.
- El `Restaurant Settings` original no se elimina ni se vacía.
- No se borran series, órdenes, fulfillments, objetos ni facturas.

## Test Matrix

| Área | Casos |
|---|---|
| Resolución | documento, POS Profile, empresa activa, empresa ausente |
| Migración | primera ejecución, repetición, sitio con una y varias empresas |
| Objetos | ambiente, mesa heredada, centro heredado, relación cruzada rechazada |
| Mesas | lista, contador, alta, transferencia y permisos por empresa |
| Producción | comandas, consolidación, atendidos y transición por empresa |
| Delivery | habilitación, tarifa y tablero por empresa |
| Factura | series, formatos e impuestos desde empresa de la orden |
| Realtime | dos sesiones con empresas diferentes |
