# Paso 6 — Bucle de seguimiento frame a frame

## Rama
`feature/rope-jump-counter`

## Descripción
Integrar `ShoeTracker` en un bucle de vídeo en vivo, con manejo explícito de "zapato perdido" (sale de cuadro, oclusión, mala luz puntual) para que el sistema no se quede colgado ni cuente saltos falsos cuando no hay detección fiable.

## Cómo hacerlo
1. Bucle principal: leer frame (reutilizando `Camera.read()` de `lse_auth/camera.py`, ver Paso 13), llamar a `ShoeTracker.update(frame)`.
2. Si no hay detección válida (ningún contorno pasa los filtros del Paso 4) durante `N` frames seguidos, marcar estado `PERDIDO` y dejar de alimentar la señal de posición del Paso 7 con valores inventados — mejor un hueco en la señal que un valor erróneo.
3. Si vuelve a detectarse, marcar estado `SEGUIMIENTO` y seguir normal.
4. Medir aquí la tasa de refresco real (FPS) del bucle completo (segmentación + tracking + overlay) — el guion valora que no se vea comprometida, así que es buen punto para detectar cuellos de botella pronto, no al final.

## Qué necesita estar hecho antes
Paso 5 (`ShoeTracker` implementado).

## Entregable del paso
Bucle de prueba `jump_tracker/demo_standalone.py` que abre la cámara, corre el tracker y muestra el bounding box en vivo, con el estado (`SEGUIMIENTO`/`PERDIDO`) impreso en consola.
