# Paso 5 — Elección e inicialización del tracker

## Rama
`feature/rope-jump-counter`

## Descripción
El guion pide explícitamente un "tracker" que muestre una bounding box alrededor de la zona de interés y la siga mientras se mueve — no basta con redetectar el blob cada frame de forma independiente (aunque para este caso concreto, "redetectar cada frame con el Paso 3+4" es en sí mismo una forma válida de tracking por color, y es más simple que un tracker genérico). Aquí se decide el enfoque.

## Cómo hacerlo
Dos opciones razonables, elegir una y justificarla en el informe:

1. **Tracking por detección (recomendado para empezar)**: en cada frame, volver a correr segmentación + blob (Pasos 3-4) y usar la posición anterior solo como ayuda para desambiguar entre varios candidatos (ya previsto en el Paso 4). Es robusto a que el zapato cambie de forma aparente al moverse, y es clásico (no depende de un tracker de caja negra de OpenCV).
2. **Tracker dedicado de OpenCV** (`cv2.TrackerCSRT_create()` o `cv2.TrackerKCF_create()`): se inicializa una vez con la bounding box del Paso 4 y el tracker se encarga de seguirla frame a frame sin volver a segmentar. Más ligero en CPU si va bien, pero puede perder el objeto si el zapato se mueve muy rápido (típico en un salto) y hay que detectar cuándo se ha perdido para reinicializar.

Para un contador de saltos, donde el movimiento es rápido y vertical, la opción 1 (redetección por color cada frame) suele ser más fiable y más fácil de depurar — pero si se usa la 2, hay que implementar un chequeo de confianza del tracker y reinicializarlo con el Paso 3-4 cuando la pierda.

## Qué necesita estar hecho antes
Paso 4 funcionando de forma fiable sobre los vídeos de referencia.

## Entregable del paso
Decisión documentada aquí (con justificación breve) + clase `ShoeTracker` en `jump_tracker/tracker.py` con un método `update(frame) -> bbox, center` que implementa la opción elegida.
