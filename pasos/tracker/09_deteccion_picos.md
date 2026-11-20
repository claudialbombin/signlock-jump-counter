# Paso 9 — Detección de picos (saltos)

## Rama
`feature/rope-jump-counter`

## Descripción
Convertir la señal suavizada del Paso 8 en eventos discretos de "salto". Esta es la pieza central del contador: cada pico claro de la señal (el zapato sube y vuelve a bajar) cuenta como un salto.

## Cómo hacerlo
1. Enfoque simple por umbral + flanco: definir una altura mínima `H_MIN` (en píxeles, calibrada con los datos del Paso 1/2) que el centroide debe superar para considerar que "ha empezado un salto", y detectar el cruce ascendente y luego el descendente de ese umbral como un ciclo completo de salto.
2. Alternativa más robusta si hay tiempo: `scipy.signal.find_peaks` sobre la señal suavizada, con los parámetros `height` (altura mínima del pico) y `distance` (frames mínimos entre dos picos, para que dos vibraciones seguidas del mismo salto no cuenten como dos) — evita escribir la lógica de flancos a mano.
3. Exigir un tiempo mínimo entre saltos (`distance` o un temporizador propio) acorde a la cadencia humana real de salto (normalmente no se puede saltar más de ~3-4 veces por segundo) — esto descarta de raíz mucho ruido de alta frecuencia sin tener que afinar tanto el umbral de altura.
4. Probar estos parámetros contra los vídeos del Paso 2 y comparar el conteo automático contra el `conteo_real.md` anotado a mano.

## Qué necesita estar hecho antes
Paso 8 (señal suavizada) y haber anotado el número real de saltos de los vídeos de prueba (Paso 2).

## Entregable del paso
Función `detect_jumps(series, h_min, min_interval) -> lista de timestamps de salto` en `jump_tracker/jump_detector.py`, con una primera medición de precisión sobre los vídeos de referencia.
