## 1. Modelo y migración

- [x] 1.1 Definir arquitectura y criterios de aislamiento.
- [x] 1.2 Crear `Restaurant Company Settings` con empresa única.
- [x] 1.3 Crear resolvedor central y compatibilidad legado acotada.
- [x] 1.4 Agregar patch idempotente de configuración y objetos existentes.

## 2. Integración operativa

- [x] 2.1 Resolver restricciones, delivery, impresión y series por empresa.
- [x] 2.2 Agregar empresa a ambientes, mesas y centros de producción.
- [x] 2.3 Filtrar alta, consulta, contadores y permisos por empresa.
- [x] 2.4 Validar transferencia, órdenes y producción contra cruces de empresa.
- [x] 2.5 Incorporar empresa en actualizaciones realtime globales.
- [x] 2.6 Mostrar un estado vacío accionable para crear el primer ambiente de una empresa.
- [x] 2.7 Recuperar la empresa activa desde el permiso predeterminado cuando Frappe no conserve el valor personal.
- [x] 2.8 Configurar una serie y correlativo independiente para Table Order por empresa.

## 3. Validación

- [x] 3.1 Agregar pruebas del resolvedor, validaciones y migración.
- [x] 3.2 Ejecutar validación Python, JavaScript, JSON y OpenSpec.
- [x] 3.3 Ejecutar migrate y pruebas en `v15.local`.
- [x] 3.4 Configurar la segunda empresa, su POS Profile, objetos y apertura por cajero.
- [x] 3.5 Validar visualmente dos empresas en sesiones separadas sin mezclar ambientes.
- [ ] 3.6 Ejecutar el flujo completo mesa, orden, Production Center y pago en ambas empresas.
- [ ] 3.7 Validar impuestos, descuentos, boleta/factura, series e impresión por empresa.
- [ ] 3.8 Probar realtime entre navegadores y rechazo explícito de transferencia entre empresas.
- [x] 3.9 Validar series independientes de Table Order y migrarlas en `v15.local`.
