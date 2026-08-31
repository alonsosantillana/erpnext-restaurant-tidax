## 1. Format

- [x] 1.1 Crear el Print Format fiscal de 80 mm.
- [x] 1.2 Agregar QR local y propina separada.

## 2. Configuration

- [x] 2.1 Crear Silent Print Format de 80 mm mediante parche idempotente.
- [x] 2.2 Migrar configuraciones y rutas antiguas sin sobrescribir formatos personalizados.

## 3. Validation

- [x] 3.1 Validar JSON, Python y OpenSpec.
- [x] 3.2 Ejecutar migrate y pruebas automatizadas en v15.local.
- [x] 3.3 Generar y revisar un PDF real de comprobante.
- [x] 3.4 Realizar impresion fisica en POS-80-Series.

## 4. Native ESC/POS

- [x] 4.1 Agregar transporte configurable PDF o ESC/POS por ruta.
- [x] 4.2 Generar factura fiscal RAW con QR, corte, CP850 y copias.
- [x] 4.3 Migrar rutas INVOICE existentes a ESC/POS.
- [x] 4.4 Agregar pruebas del generador y payload.
- [ ] 4.5 Calificar impresion fisica ESC/POS en POS-80-Series.
- [x] 4.6 Generar precuenta ACCOUNT RAW no fiscal y migrar sus rutas.
- [x] 4.7 Agregar pruebas del formato ACCOUNT ESC/POS.
