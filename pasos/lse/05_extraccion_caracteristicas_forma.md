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
   - O: la referencia real (ver `pasos/lse/referencia_lse/letra_O_foaps.png`) muestra pulgar e índice tocándose (hueco pequeño, visto en el Paso 4) **más 3 dedos extendidos** (corazón, anular, meñique) con sus propios defectos de convexidad entre ellos. Es decir, O no se reconoce solo por `has_hole`: se reconoce por `has_hole == True` **y** un número de defectos entre dedos sueltos de ~2 (entre corazón-anular y anular-meñique), distinto de L (1 defecto grande pulgar-índice, sin hueco) y de H (1 defecto pequeño índice-corazón, sin hueco).
2. **Relación de aspecto** del bounding box (ancho/alto): la L y la H tienden a ser más alargadas/horizontales que el puño compacto de la A.
3. **Solidity** = área del contorno / área del convex hull: la O y la A (sin dedos sueltos) tienden a tener solidity alta; L y H, más baja por los dedos separados.
4. Opcional: ángulo de orientación de la mano vía `cv2.fitEllipse` o PCA, por si se pide a la persona mantener la mano más o menos recta.

## Qué necesita estar hecho antes
Paso 4 (contorno + bounding box + `has_hole`).

## Entregable del paso
Función `extract_features(contour, bbox, has_hole) -> dict` (o dataclass) con: `n_defects`, `defect_angles`, `aspect_ratio`, `solidity`, `has_hole`. Probarla contra el dataset del Paso 2 e imprimir una tabla de valores por clase para confirmar que las 4 letras se separan razonablemente bien.

## Implementación (21/11)
En vez de contar *convexity defects* (sensibles a pequeños entrantes del contorno), se detectan directamente los **dedos estirados**:
- **Punta** = punto del contorno cuya distancia al centro de la palma es un **máximo local** y supera **2 × radio de la palma** (un dedo doblado se queda cerca de la palma). Puntas a menos de 0,5 radios entre sí son el mismo dedo.
- Se aceptan puntas más cortas (1,7–2 radios) o que apuntan por debajo de la horizontal (> 180°) **solo si son finas** (< 0,8 radios): así entra un pulgar pegado o bajo, pero no los nudillos, el círculo de la O ni la esquina de la muñeca, que son igual de cortos pero el doble de anchos.
- Las puntas **en el borde del ROI** son formas cortadas y se descartan. Si la mano toca el borde por encima de la palma, `cut = True` y el clasificador no decide.
- Por cada dedo:
  - **ángulo** (0° = derecha, 90° = arriba, 180° = izquierda, sobre la imagen en espejo);
  - **anchura**: distancia entre los dos puntos del contorno que están a 1 radio de palma de la punta, uno a cada lado, siguiendo el contorno. **Dos dedos pegados se ven como un dedo el doble de ancho**;
  - **longitud** (punta–centro).
- **Agujero de la O** (`o_hole`): un agujero de al menos 0,08 radios² en el lado del pulgar (90–200°). Los huecos falsos de la segmentación son más pequeños (0,01–0,05) y salen en otro sitio.
- Todo va dividido por el radio de la palma, así no depende de lo lejos que esté la mano.

Valores medidos (anchura en radios de palma):

| | Dedos (ángulo / anchura) |
|---|---|
| L (Tere) | índice 92–97° / 0,45–0,47 · pulgar 156–161° / 0,50–0,56 |
| L (Claudia) | índice ~115° / 0,45 · pulgar ~190° / 0,63 |
| H (Tere, dedos separados) | 18–25° y 33–49° / 0,36–0,63 · pulgar 112–128° / 0,47–0,61 |
| H (Claudia, dedos pegados) | 36–40° / **0,80–0,92** · pulgar 121–137° / 0,46–0,50 |
| O (Tere) | 19–21°, 54–58°, 76–79° / 0,38–0,53 · agujero 0,12–0,13 r² a ~139° |
| O (Claudia, de frente) | 3 puntas a ~77°, 91° y 106° (dedos medio pegados), sin agujero |
| O (Claudia, girada) | 3 puntas + el círculo a ~171° / 1,03 · agujero 0,24 r² a ~150° |

Código: `lse_auth/features.py` → `extract_features(hand) -> HandFeatures` (lista de `Finger`, `o_hole`, `cut`).
