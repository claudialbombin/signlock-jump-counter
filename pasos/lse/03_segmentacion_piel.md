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

## Implementación (21/11)
- `lse_auth/segmentation.py`:
  - `BackgroundModel`: media de `BG_FRAMES` = 30 frames de la escena vacía; `reset()` para volver a tomarlo.
  - `match_brightness`: la webcam cambia sola la exposición y el balance de blancos al entrar la mano (la imagen sale ~20 niveles más clara que el fondo). Se corrige con una **función de transferencia de brillo** por canal (Javed et al., 2005): para cada intervalo de valores del fondo se toma la mediana de esos mismos píxeles en el frame actual y se interpola una LUT. Una ganancia global no bastaba: la pared blanca, la verde y la madera cambian distinto.
  - `segment_hand(frame, background)`: diferencia en YCrCb con `score = 0,5·|ΔY| + |ΔCr| + |ΔCb|` (> 25) → cierre (31 px, hecho a media resolución) + relleno de huecos → AND con el rango de piel `Cr 135–180, Cb 85–135` → apertura (5) + cierre (9). Con `debug=True` devuelve también los pasos intermedios.
  - El relleno de huecos va **antes** del AND con la piel: así el palmar queda entero, y el agujero de la O (que es pared, no piel) se conserva.
- Parámetros en `lse_auth/config.py` (sección *Hand segmentation*), cada uno con su justificación.
- `lse_auth/segmentation_preview.py`: vista en directo (`f` fondo, `s` guardar secuencia, FPS en pantalla), `--dataset` (todas las imágenes con fondo) y `--sequence CLASE/img_XX.jpg` (figura para el informe).

## Resultados con la segunda captura (H, O, L de Tere)
| Clase | Imágenes | Área de la mano (px) | Mayor componente con agujero |
|---|---|---|---|
| H | 20 | 39.928 – 66.841 | 1/20 |
| O | 15 | 50.214 – 51.930 | **15/15** |
| L | 19 | 39.332 – 48.178 | 0/19 |

- La O conserva el agujero en todas las imágenes, que es justo la pista que usará el Paso 4/5.
- Tiempo: mediana **13 ms/frame** (ROI de 448×504) en el portátil de Claudia.
- Figura de la secuencia de transformación: `pasos/lse/figuras/secuencia_O_img_40.png`.
- **A y NONE no sirven todavía**: la cámara se movió ~18 px tras guardar el fondo, así que la resta marca todos los bordes de la pared y la estantería (pendiente de repetir, ver PR #7 / issue #6).

## Limitaciones conocidas
- Quedan restos pequeños en el borde de la estantería (esquina superior derecha del ROI); son componentes separadas y el Paso 4 se queda con la mayor.
- La manga y el antebrazo entran por abajo del ROI: el Paso 4 tendrá que cortar a la altura de la muñeca.
- Si la mano ocupa más de la mitad de un rango de colores del ROI, la LUT de brillo se contamina un poco (se ve como un tinte rosado en el fondo corregido). No afecta al resultado final en el dataset actual; si diera problemas, se puede estimar la LUT solo con píxeles fuera de la máscara del frame anterior.
