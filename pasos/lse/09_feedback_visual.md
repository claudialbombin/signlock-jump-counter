# Paso 9 — Feedback visual en pantalla

## Rama
`feature/sign-language-auth`

## Descripción
El usuario necesita ver en tiempo real qué está pasando: qué letra se está detectando ahora mismo, cuánto lleva de la secuencia H-O-L-A, y si está bloqueado o desbloqueado. Esto también es lo que luego se graba para el vídeo-demo del entregable.

## Cómo hacerlo
1. Sobre el frame de salida, dibujar con `cv2.putText`/`cv2.rectangle`:
   - El bounding box y el contorno de la mano (reutilizando el Paso 4), en un color si está "reconociendo" y en otro si ya ha confirmado letra.
   - La letra detectada en el frame actual (aunque no esté aún confirmada), p. ej. en pequeño y gris.
   - El progreso de la secuencia como texto tipo `H-O-_-_ ` (usar el estado de `SequenceDecoder`).
   - Un mensaje grande de estado: `BLOQUEADO` (rojo) / `DESBLOQUEADO` (verde), ocupando una esquina fija de la pantalla.
2. Si se resetea la secuencia por error, mostrar brevemente un mensaje tipo "Secuencia incorrecta, inténtalo de nuevo" (2-3 segundos) antes de volver al estado normal.
3. Mantenerlo ligero (nada de overlays pesados) para no comprometer la tasa de refresco — el guion valora explícitamente que no se vea afectada.

## Qué necesita estar hecho antes
Paso 8 (`SequenceDecoder` con estado consultable) y Paso 4 (contorno/bbox para dibujar).

## Entregable del paso
Función `draw_overlay(frame, contour, bbox, current_letter, decoder_state) -> frame` en `lse_auth/overlay.py`.
