# Paso 2 — Captura del set de imágenes de referencia

## Rama
`feature/sign-language-auth`

## Descripción
Capturar, con la cámara ya calibrada (ver `calibration_main.py` / `calibration_functions.py` en `main`), una pequeña colección de imágenes/frames de cada una de las 4 señas (H, O, L, A) más una clase "fondo/mano neutra" (ninguna seña). Este set sirve para ajustar a ojo los umbrales de segmentación y para probar el clasificador de forma repetible, sin depender de tener la mano delante en cada prueba.

No es un dataset de entrenamiento de deep learning (no toca, el guion del proyecto pide visión clásica y avisa de consultar con los profesores si se usa deep learning) — es solo material de referencia y de test de regresión manual.

## Cómo hacerlo
1. Reutilizar el script de captura de cámara (`2test.py` o el futuro `camera_io.py` de integración) para grabar o guardar fotos sueltas con una tecla (ej. `c` para capturar, `0-4` para etiquetar la clase).
2. Capturar ~15-20 imágenes por clase (H, O, L, A, ninguna), variando ligeramente posición de la mano dentro del encuadre y, si se puede, iluminación.
3. Guardarlas en `pasos/lse/dataset_lse/<clase>/img_XX.jpg` dentro del repo (o fuera si pesan mucho — en ese caso documentar dónde están y añadir el patrón a `.gitignore`).
4. Aplicar a cada imagen la corrección de distorsión de la calibración (`cv2.undistort` con los `intrinsics`/`dist_coeffs` del Paso de calibración) antes de guardarla, para que el set de referencia ya esté en condiciones realistas de uso.

## Qué necesita estar hecho antes
- Paso 1 (saber exactamente qué forma de mano buscar).
- Calibración de cámara ya mergeada en `main` (rama `feature/calibration`, ya integrada vía PR #1) — se necesitan `intrinsics` y `dist_coeffs` guardados (recomendable: exportarlos a un `.npz`/`.yaml` en vez de recalcular cada vez).

## Implementación
- `calibration_main.py` ahora exporta el resultado a `calibration/camera_params.npz` (K, coeficientes de distorsión, tamaño 2560x1440 y RMS = 1,367 px; Tere recalibró el 20/11 con su cámara → RMS = 1,195 px). No hace falta recalibrar cada vez.
- `lse_auth/calibration_io.py`: guardar/cargar los parámetros y **reescalar K** a la resolución de captura (1280x720 → factor 0,5; los coeficientes de distorsión no cambian).
- `lse_auth/camera.py`: clase `Camera` (abre la cámara con el backend de cada SO) + `Undistorter`, que precalcula los mapas con `initUndistortRectifyMap` y aplica `remap` (~2 ms/frame en vez de `cv2.undistort` en cada frame). Orden: **primero corregir distorsión, luego espejo**.
- `lse_auth/dataset.py`: guardar/listar imágenes por clase y hoja resumen (`overview.jpg`).
- `lse_auth/capture_dataset.py`: herramienta de captura (instrucciones en `pasos/lse/dataset_lse/README.md`).
- ROI fija de la mano en `config.HAND_ROI` (se dibuja como guía al capturar y se usará en el Paso 3).

## Primera captura (20/11) y lo que se aprendió
- Tere capturó 114 imágenes (A 20, H 22, L 22, O 25, NONE 25) con su cámara, recalibrada ese mismo día.
- Al probar la segmentación por color de piel (Paso 3) falló: la **madera de la estantería y la pared con luz cálida tienen el mismo Cr/Cb que la piel**. Se probaron umbrales fijos en YCrCb, balance de blancos gray-world y retroproyección de histograma, y en las fotos de A y L la mano se perdía.
- Además, en muchas fotos la mano estaba fuera del recuadro y se veía el brazo entero.
- **Decisión**: el Paso 3 resta una foto de la escena vacía y después filtra por piel. Por eso la herramienta de captura ahora obliga a guardar el fondo (`f`) al empezar cada sesión y enlaza cada imagen con su fondo en `backgrounds.csv`.

## Pendiente (manual)
- Repetir la captura con la cámara fija, fondo guardado con `f`, mano derecha dentro del recuadro y el mínimo de brazo (instrucciones en `pasos/lse/dataset_lse/README.md`). Comprobar con `--summary`.
- Las imágenes antiguas (sin fondo) se quedan como referencia, pero el ajuste del Paso 3 usa solo las que tienen fondo.

## Entregable del paso
Carpeta `pasos/lse/dataset_lse/` con las imágenes etiquetadas por carpeta, ya corregidas de distorsión.
