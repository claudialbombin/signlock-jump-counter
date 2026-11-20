# Paso 10 — Lógica de conteo en tiempo real

## Rama
`feature/rope-jump-counter`

## Descripción
El Paso 9 detecta picos sobre una señal ya grabada/completa (útil para medir precisión offline); aquí se traslada esa misma lógica a un contador que funciona en vivo, frame a frame, sin esperar a tener toda la señal.

## Cómo hacerlo
1. Mantener una pequeña máquina de estados: `ABAJO` (zapato cerca del suelo, por debajo de `H_MIN`) → `SUBIENDO` (cruza `H_MIN` hacia arriba) → `ABAJO` otra vez (vuelve a cruzar hacia abajo) = **1 salto contado**, incrementar el contador en esa transición concreta (no en la subida, para no contar el salto antes de que termine).
2. Aplicar el mismo tiempo mínimo entre saltos del Paso 9 como "debounce": ignorar un nuevo cruce ascendente si ha pasado menos de `min_interval` desde el último salto contado — evita contar de más por rebotes o ruido justo después de un salto real.
3. Exponer el contador como un valor consultable en cualquier momento (`JumpCounter.count`), no solo como print — lo necesita el Paso 11 para el overlay.
4. Añadir un método `reset()` por si se quiere reiniciar el conteo (nueva sesión de saltos) sin reiniciar todo el programa.

## Qué necesita estar hecho antes
Paso 9 (umbral y tiempo mínimo entre saltos ya decididos y probados offline) y Paso 8 (señal suavizada disponible en vivo).

## Entregable del paso
Clase `JumpCounter` en `jump_tracker/jump_detector.py` con `update(timestamp, smoothed_y) -> bool` (devuelve `True` el frame exacto en que se cuenta un salto nuevo) y atributo `count`.
