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

## Cambio de método (20/11): fondo + piel
Con las primeras fotos, el color de piel por sí solo no separa la mano de la madera ni de la pared con luz cálida (ver Paso 2). El método queda así:

1. **Fondo de referencia**: con el ROI vacío se promedian ~30 frames de la escena (tecla `f`, igual que en la captura). Se vuelve a tomar si cambia la luz o se mueve la cámara.
2. **Resta de fondo**: diferencia absoluta frame − fondo en YCrCb dentro del ROI y umbral. Sobrevive solo lo que ha cambiado (la mano), aunque el fondo sea del color de la piel.
3. **Filtro de piel**: intersección con un rango Cr/Cb amplio, para quitar sombras de la mano sobre la pared y objetos que no son piel (manga, reloj).
4. **Morfología**: apertura + cierre, y nos quedamos con la componente más grande (eso ya es el Paso 4).

Requisito para la demo: **cámara quieta**. Es lo mismo que pide el bloque del tracker, así que no añade ninguna restricción nueva.

## Qué necesita estar hecho antes
- Paso 2 (dataset de referencia para ajustar umbrales).
- Pipeline de captura de vídeo + corrección de distorsión funcionando (normalmente vive en `feature/integration`, pero aquí basta con tener una función local `get_frame()` de usar y tirar mientras se desarrolla en aislado).

## Entregable del paso
Función `segment_hand(frame, background) -> mask` (resta de fondo + piel) en un nuevo módulo, p. ej. `lse_auth/segmentation.py`, con los umbrales ya ajustados y comentados.
