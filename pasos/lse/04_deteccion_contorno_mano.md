# Paso 4 — Detección del contorno de la mano

## Rama
`feature/sign-language-auth`

## Descripción
A partir de la máscara binaria del Paso 3, aislar el contorno que corresponde a la mano (descartando ruido residual) y quedarse con una representación limpia (contorno + bounding box) lista para extraer características.

## Cómo hacerlo
1. `cv2.findContours` sobre la máscara (modo `RETR_TREE` para poder ver también contornos internos — importante para detectar el "agujero" de la seña O — y `CHAIN_APPROX_SIMPLE`).
2. Quedarse con el contorno de mayor área (`cv2.contourArea`) como candidato a mano; descartar si el área es menor que un umbral mínimo (evita activarse con ruido cuando no hay mano en el ROI).
3. Calcular y guardar: `cv2.boundingRect` (para dibujar y para la relación de aspecto), y si `RETR_TREE` devuelve jerarquía, comprobar si ese contorno tiene un hijo (contorno interior) — eso es la pista fuerte para la seña O.
4. Dibujar el contorno y el bounding box sobre el frame para depuración visual (esto además es justo lo que pide la Sección "Secuencia de transformación de la imagen" del informe: máscara → contorno → resultado).

## Qué necesita estar hecho antes
Paso 3 (`segment_skin`) funcionando y devolviendo máscaras limpias.

## Entregable del paso
Función `find_hand_contour(mask) -> contour, bbox, has_hole` en `lse_auth/segmentation.py` (o `contours.py`).

## Implementación (21/11)
- `lse_auth/contours.py` → `find_hand_contour(mask) -> HandContour | None` con `contour`, `bbox`, `area`, `has_hole`, `palm_center`, `palm_radius`.
- Se queda con la **componente conexa más grande** (descarta los restos del borde de la estantería) y exige un área mínima de 8000 px para considerarla mano.
- `RETR_CCOMP` da el contorno exterior y sus agujeros; un agujero > 300 px es el círculo de la O.
- **Centro de la palma** = máximo de la transformada de distancia, y su valor es el radio de la palma. Es mucho más estable que el centroide, que se va hacia el brazo o los dedos.
- Para ir rápido se trabaja solo en el rectángulo que contiene la máscara: los pasos 4–6 tardan ~3 ms/frame.
- `HandContour.roi` guarda el recuadro y `touches_roi_border(p)` dice si un punto está en su borde: lo usa el Paso 5 para no tomar por dedo una forma cortada por el recuadro.
