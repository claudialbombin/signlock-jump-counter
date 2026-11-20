# Paso 8 — Suavizado de la señal

## Rama
`feature/rope-jump-counter`

## Descripción
La señal cruda de altura tiene ruido de píxel a píxel (temblor de la segmentación, saltos de 1-2 px del centroide) que puede generar picos falsos en el Paso 9 si no se suaviza antes.

## Cómo hacerlo
1. Aplicar un suavizado simple sobre la ventana reciente del buffer del Paso 7: media móvil (`numpy.convolve` con una ventana de 3-5 frames) es suficiente y barato; un filtro Savitzky-Golay (`scipy.signal.savgol_filter`) da mejor resultado si hay tiempo y `scipy` ya está entre las dependencias del proyecto.
2. Cuidado con la ventana demasiado grande: suaviza el ruido pero también "aplana" el pico real del salto y puede hacer que el Paso 9 lo pierda — ajustar viendo la gráfica de depuración del Paso 7 con y sin suavizado.
3. Si se usa la opción de redetección por color del Paso 5, el suavizado también ayuda a absorber los huecos cortos de 1 frame donde el blob no se detecta bien sin tener que tratarlos como "perdido" de verdad.

## Qué necesita estar hecho antes
Paso 7 (señal cruda disponible).

## Entregable del paso
Función `smooth(series, window=5) -> series suavizada` en `jump_tracker/signal.py`, con una comparación visual (gráfica) antes/después guardada como referencia.
