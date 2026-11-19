# Paso 5 — Extracción de características geométricas de la seña

## Rama
`feature/sign-language-auth`

## Descripción
Convertir el contorno de la mano en un pequeño vector de características numéricas que luego el Paso 6 usará para decidir "esto es H / O / L / A / nada". Esta es la parte de "método de detección de patrones" que el guion del proyecto pide explicar y justificar en el informe.

## Cómo hacerlo
Para el contorno obtenido en el Paso 4, calcular:

1. **Convex hull y convexity defects**: `cv2.convexHull(contour, returnPoints=False)` + `cv2.convexityDefects`. Contar cuántos defectos tienen una profundidad y un ángulo (ley del coseno entre los tres puntos del defecto) compatibles con un "valle entre dos dedos" → aproxima el número de dedos extendidos.
   - A ≈ 0 dedos separados (puño).
   - L ≈ 1 separación clara (entre pulgar e índice), en ángulo ~90°.
   - H ≈ 1 separación pequeña entre índice y corazón, pero con dedos paralelos (ángulo pequeño) — aquí es donde H y L se pueden confundir si solo miras "número de defectos": el ángulo del defecto es lo que las distingue.
   - O: la referencia real (ver `pasos/referencia_lse/letra_O_foaps.png`) muestra pulgar e índice tocándose (hueco pequeño, visto en el Paso 4) **más 3 dedos extendidos** (corazón, anular, meñique) con sus propios defectos de convexidad entre ellos. Es decir, O no se reconoce solo por `has_hole`: se reconoce por `has_hole == True` **y** un número de defectos entre dedos sueltos de ~2 (entre corazón-anular y anular-meñique), distinto de L (1 defecto grande pulgar-índice, sin hueco) y de H (1 defecto pequeño índice-corazón, sin hueco).
2. **Relación de aspecto** del bounding box (ancho/alto): la L y la H tienden a ser más alargadas/horizontales que el puño compacto de la A.
3. **Solidity** = área del contorno / área del convex hull: la O y la A (sin dedos sueltos) tienden a tener solidity alta; L y H, más baja por los dedos separados.
4. Opcional: ángulo de orientación de la mano vía `cv2.fitEllipse` o PCA, por si se pide a la persona mantener la mano más o menos recta.

## Qué necesita estar hecho antes
Paso 4 (contorno + bounding box + `has_hole`).

## Entregable del paso
Función `extract_features(contour, bbox, has_hole) -> dict` (o dataclass) con: `n_defects`, `defect_angles`, `aspect_ratio`, `solidity`, `has_hole`. Probarla contra el dataset del Paso 2 e imprimir una tabla de valores por clase para confirmar que las 4 letras se separan razonablemente bien.
