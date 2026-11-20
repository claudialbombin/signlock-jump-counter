# Paso 7 — Extracción de la señal de posición vertical

## Rama
`feature/rope-jump-counter`

## Descripción
Convertir la secuencia de centroides del Paso 6 en una señal 1D (altura del zapato a lo largo del tiempo), que es la que se va a analizar para contar saltos. Trabajar en esta señal simplificada es mucho más manejable que razonar directamente sobre bounding boxes.

## Cómo hacerlo
1. Mantener un buffer (p. ej. `collections.deque` con tamaño máximo, o una lista que se recorta) con `(timestamp, cy)` de cada frame con detección válida — usar la coordenada `y` del centroide, invertida si hace falta para que "subir" sea "aumentar" en la gráfica (más intuitivo para depurar).
2. Saltar (no añadir nada) en los frames marcados como `PERDIDO` por el Paso 6, en vez de interpolar a ciegas — mejor tratarlo explícitamente en el Paso 9.
3. Como ayuda de depuración, usar `matplotlib` para volcar esta señal a un PNG después de correr un vídeo de prueba del Paso 2 — ver a simple vista si los picos de los saltos son claros antes de meterse en detección automática de picos.

## Qué necesita estar hecho antes
Paso 6 (bucle de seguimiento con centroides frame a frame).

## Entregable del paso
Función/clase `PositionBuffer` en `jump_tracker/signal.py` con un método `add(timestamp, cy)` y `get_series() -> arrays de tiempos y alturas`.
