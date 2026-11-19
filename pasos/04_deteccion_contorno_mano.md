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
