# Paso 4 — Detección del blob del zapato y filtrado por forma

## Rama
`feature/rope-jump-counter`

## Descripción
A partir de la máscara binaria del Paso 3, quedarse con el contorno que realmente es el zapato (no ruido ni otra mancha oscura) y calcular su bounding box y centroide, que es lo que se va a seguir en los pasos siguientes.

## Cómo hacerlo
1. `cv2.findContours` sobre la máscara (`RETR_EXTERNAL` basta, no hace falta jerarquía aquí).
2. Filtrar candidatos por:
   - **Área mínima y máxima** (descarta ruido suelto y manchas enormes como una sombra grande).
   - **Relación de aspecto** típica de un zapato visto de perfil o desde arriba (más ancho que alto, o al revés según el ángulo de cámara — medirlo en los vídeos del Paso 2).
   - Si hay varios candidatos plausibles, quedarse con el más cercano a la posición del zapato en el frame anterior (continuidad temporal) en vez del de mayor área a secas — evita saltar a otra mancha oscura puntual.
3. Calcular `cv2.boundingRect` y el centroide (`cv2.moments` → `cx, cy`, o simplemente el centro del bounding box si el contorno es razonablemente compacto).
4. Dibujar el contorno y bounding box sobre el frame para depuración visual — esto además es la base de la "secuencia de transformación de la imagen" que pide el informe para este bloque.

## Qué necesita estar hecho antes
Paso 3 (`segment_shoe` devolviendo máscaras limpias).

## Entregable del paso
Función `find_shoe_blob(mask, previous_center=None) -> bbox, center` en `jump_tracker/segmentation.py`.
