# Paso 2 — Captura de vídeo de referencia

## Rama
`feature/rope-jump-counter`

## Descripción
Grabar (o reutilizar los del Paso 1) un pequeño set de vídeos de referencia para poder ajustar umbrales de color y de altura de salto de forma repetible, sin depender de saltar en vivo cada vez que se prueba el código.

## Cómo hacerlo
1. Reutilizar el wrapper de cámara ya existente en el repo (`lse_auth/camera.py`, clase `Camera`) en vez de escribir otro desde cero — ya aplica la corrección de distorsión de la calibración y el espejado. Ver Paso 13 sobre cómo compartir esta pieza sin acoplar las dos ramas.
2. Grabar 3-4 vídeos de ~15-20 s: saltos seguidos a ritmo normal, saltos lentos, una pausa en medio (para comprobar que no cuenta saltos de más durante el reposo), y uno con algo de ruido de fondo (otra persona moviéndose, sombras).
3. Guardarlos en `pasos/tracker/videos_referencia/` (si pesan mucho, documentar aquí dónde están y añadir el patrón a `.gitignore` en vez de subirlos al repo).
4. Anotar a mano, para cada vídeo, el número real de saltos — es el "ground truth" que se usará en el Paso 14 para medir aciertos.

## Qué necesita estar hecho antes
Paso 1 (saber qué zapato y qué encuadre usar). Calibración de cámara ya disponible en `calibration/camera_params.npz` (rama `feature/calibration`, ya en `main`).

## Entregable del paso
Carpeta `pasos/tracker/videos_referencia/` con los vídeos y un fichero `conteo_real.md` con el número de saltos real de cada uno.
