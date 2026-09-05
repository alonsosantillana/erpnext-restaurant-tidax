# Diferenciar acciones de producción por color

## Problema

Los botones `Iniciar plato` y `Completar plato` usan el mismo aspecto neutro. En cocina
esto dificulta reconocer rápidamente si la acción inicia la preparación o confirma que
el plato ya está listo.

## Solución

Mantener `Iniciar plato` con apariencia neutra y mostrar `Completar plato` en verde. El
texto y la transición de estado continúan siendo la fuente funcional de la acción; el
color aporta una señal visual adicional.

## Alcance

- Botones individuales de platos en la vista de producción.
- Estados pendiente y en preparación.

## Fuera de alcance

- Cambiar el flujo o los permisos de producción.
- Modificar los botones masivos de comandas.
