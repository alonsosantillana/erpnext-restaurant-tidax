# Validación

## Resultado automático

- JSON de los tres DocTypes modificados: válido.
- `node --check public/js/resto_gastos.js`: correcto.
- `python3 -m py_compile`: correcto.
- `git diff --check`: correcto.
- `test_pos_series`: 11 pruebas correctas.
- `test_resto_gastos`: 5 pruebas correctas.
- `bench --site v15.local migrate`: correcto.

## Datos verificados tras migración

- ADDERA PERU SAC: `GTO-ADA-.YYYY.-.#####`.
- ERPCLOUD SAC: `GTO-ECS-.YYYY.-.#####`.
- Existen aperturas POS abiertas para los perfiles `Resto` y `Resto2`.
- Existe al menos un artículo habilitado del grupo `GASTOS` (`GTO-001`).

## Limitación del entorno

`openspec validate make-resto-gastos-multicompany` no puede ejecutarse porque la
versión instalada de OpenSpec usa expresiones regulares con flag `v`, que requieren
Node 20, mientras el servidor ejecuta Node 18.20.8. La estructura del cambio se revisó
manualmente contra los demás cambios del repositorio.

## Prueba manual pendiente

En cada empresa:

1. Abrir `Resto Gastos` con el cajero correspondiente.
2. Confirmar compañía predeterminada y seleccionar su apertura abierta.
3. Seleccionar un modo disponible, agregar `GTO-001` e indicar un importe positivo.
4. Guardar y enviar; verificar el correlativo de la empresa.
5. Confirmar que el gasto aparece solo en el `Resumen Cierre de Caja` de esa empresa.
6. Cancelar un gasto de prueba y confirmar que deja de descontarse del cierre.

## Actualización documental — 2026-11-13

Se añadieron los deltas que faltaban usando la propuesta y el diseño existentes,
contrastados con el controlador, la resolución de series y el reporte actuales.
La validación estricta ahora pasa con Node 22.23.1 ya instalado, sin actualizar
Node del bench ni realizar operaciones contra el sitio. La limitación del CLI
del apartado anterior describe el momento de la implementación histórica.

La exclusión contable original fue ampliada por `account-resto-gastos-on-submit`;
no se elimina esa decisión histórica ni se afirma que el sistema actual siga
sin asientos. La base consolidada documenta ambos contratos. Las pruebas manuales
multiempresa siguen pendientes y no se repitió ninguna migración.
