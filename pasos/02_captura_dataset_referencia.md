# Paso 2 — Captura del set de imágenes de referencia

## Rama
`feature/sign-language-auth`

## Descripción
Capturar, con la cámara ya calibrada (ver `calibration_main.py` / `calibration_functions.py` en `main`), una pequeña colección de imágenes/frames de cada una de las 4 señas (H, O, L, A) más una clase "fondo/mano neutra" (ninguna seña). Este set sirve para ajustar a ojo los umbrales de segmentación y para probar el clasificador de forma repetible, sin depender de tener la mano delante en cada prueba.

No es un dataset de entrenamiento de deep learning (no toca, el guion del proyecto pide visión clásica y avisa de consultar con los profesores si se usa deep learning) — es solo material de referencia y de test de regresión manual.

## Cómo hacerlo
1. Reutilizar el script de captura de cámara (`2test.py` o el futuro `camera_io.py` de integración) para grabar o guardar fotos sueltas con una tecla (ej. `c` para capturar, `0-4` para etiquetar la clase).
2. Capturar ~15-20 imágenes por clase (H, O, L, A, ninguna), variando ligeramente posición de la mano dentro del encuadre y, si se puede, iluminación.
3. Guardarlas en `pasos/dataset_lse/<clase>/img_XX.png` dentro del repo (o fuera si pesan mucho — en ese caso documentar dónde están y añadir el patrón a `.gitignore`).
4. Aplicar a cada imagen la corrección de distorsión de la calibración (`cv2.undistort` con los `intrinsics`/`dist_coeffs` del Paso de calibración) antes de guardarla, para que el set de referencia ya esté en condiciones realistas de uso.

## Qué necesita estar hecho antes
- Paso 1 (saber exactamente qué forma de mano buscar).
- Calibración de cámara ya mergeada en `main` (rama `feature/calibration`, ya integrada vía PR #1) — se necesitan `intrinsics` y `dist_coeffs` guardados (recomendable: exportarlos a un `.npz`/`.yaml` en vez de recalcular cada vez).

## Entregable del paso
Carpeta `pasos/dataset_lse/` con las imágenes etiquetadas por carpeta, ya corregidas de distorsión.
