# Paso 3 — Segmentación de piel / aislamiento de la mano

## Rama
`feature/sign-language-auth`

## Descripción
Primer bloque de procesado real: separar la mano del fondo en cada frame para poder luego extraer su contorno. Se hace con un umbralizado de color en un espacio robusto a cambios de iluminación (HSV o YCrCb son los habituales para piel), no con deep learning.

## Cómo hacerlo
1. Convertir el frame (ya corregido de distorsión con los parámetros de calibración) a HSV o YCrCb con `cv2.cvtColor`.
2. Definir un rango `(lower, upper)` para el tono de piel con `cv2.inRange`. Partir de valores típicos (p. ej. en YCrCb: `Cr` entre 133-173, `Cb` entre 77-127) y afinarlos con el dataset del Paso 2.
3. Aplicar operaciones morfológicas (`cv2.morphologyEx` con `MORPH_OPEN` y `MORPH_CLOSE`) para quitar ruido y rellenar huecos pequeños de la máscara.
4. Opcional pero recomendable: fijar un ROI (región de interés) fija en pantalla donde el usuario debe poner la mano, para reducir falsos positivos de otras zonas de piel (cara, brazos) — ayuda mucho a la robustez y es fácil de justificar en el informe.
5. Probar la máscara contra las imágenes del dataset de referencia y anotar qué % se segmenta limpiamente.

## Qué necesita estar hecho antes
- Paso 2 (dataset de referencia para ajustar umbrales).
- Pipeline de captura de vídeo + corrección de distorsión funcionando (normalmente vive en `feature/integration`, pero aquí basta con tener una función local `get_frame()` de usar y tirar mientras se desarrolla en aislado).

## Entregable del paso
Función `segment_skin(frame) -> mask` en un nuevo módulo, p. ej. `lse_auth/segmentation.py`, con los umbrales ya ajustados y comentados.
