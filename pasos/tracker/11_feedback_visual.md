# Paso 11 — Feedback visual en pantalla

## Rama
`feature/rope-jump-counter`

## Descripción
Mostrar en pantalla lo que pide el guion para el bloque "Tracker": la bounding box alrededor de la zona de interés siguiéndola mientras se mueve, más el contador de saltos y los FPS (el vídeo final debe incrustar la tasa de refresco en los frames).

## Cómo hacerlo
1. Dibujar sobre el frame (reutilizando el `bbox` del Paso 5/6): `cv2.rectangle` para la caja, y opcionalmente el centroide como un punto.
2. Dibujar el contador de saltos grande y legible en una esquina fija (`cv2.putText`), actualizado en cada frame desde `JumpCounter.count`.
3. Dibujar los FPS actuales (medidos como en el Paso 6) en otra esquina — requisito explícito del vídeo-demo final.
4. Si el estado es `PERDIDO` (Paso 6), mostrarlo claramente (p. ej. caja en rojo o texto "zapato no detectado") en vez de dejar una caja fantasma en la última posición conocida.
5. Opcional pero valorado por el guion como "ampliación": dibujar la trayectoria reciente del centroide (una polilínea con las últimas N posiciones) para visualizar el patrón de salto.

## Qué necesita estar hecho antes
Paso 10 (contador en vivo) y Paso 6 (bbox y estado disponibles cada frame).

## Entregable del paso
Función `draw_overlay(frame, bbox, state, jump_count, fps) -> frame` en `jump_tracker/overlay.py`.
