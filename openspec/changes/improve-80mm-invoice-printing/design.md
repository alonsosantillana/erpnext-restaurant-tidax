## Decisions

### Printable area

El documento conserva pagina fisica de 80 mm. El contenido usa 72 mm y margenes
laterales de 4 mm para tolerar controladores genericos POS-80-Series. El CSS se
aplica tanto a pantalla como a impresion y elimina el ancho historico de cuatro
pulgadas.

### Rendering

Las rutas INVOICE usan bytes ESC/POS enviados en raw_content para evitar el
escalado PDF del controlador de Windows. El ticket usa 48 columnas, CP850, QR
nativo, corte parcial y repeticion explicita por copia. PDF permanece disponible
como respaldo configurable por ruta.

### Fiscal content

La propina se consulta desde Restaurant Tip y se presenta en un bloque separado
como importe no fiscal. El total del comprobante no se altera. El QR se deriva
del valor persistido por la integracion electronica.

### Migration

El parche crea o actualiza Silent Print Format con ancho 80 mm y asigna el nuevo
formato solamente cuando la configuracion actual esta vacia o usa
`Return POS Invoice`. Una seleccion personalizada no se reemplaza.

## Compatibility

La calificacion fisica debe confirmar CP850, QR nativo y corte parcial en cada
modelo. Si una impresora no implementa ESC/POS, la ruta puede volver a PDF.
