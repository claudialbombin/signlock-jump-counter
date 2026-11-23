# Paso 6 — Clasificador por reglas (H / O / L / A / ninguna)

## Rama
`feature/sign-language-auth`

## Descripción
Con la tabla de valores por clase del Paso 5 delante, escribir un clasificador basado en reglas (si-entonces, sin machine learning) que convierta el vector de características en una etiqueta. Es deliberadamente simple e interpretable — encaja con el espíritu "visión clásica" del proyecto y es fácil de explicar y justificar en el informe.

## Cómo hacerlo
1. Mirar la tabla de valores reales del dataset (no solo la teoría del Paso 1) y fijar umbrales concretos, por ejemplo (ajustar con tus propios números):
   - Si `has_hole` → **O**.
   - Si no, y `n_defects == 0` y `solidity` alta → **A**.
   - Si no, y hay 1 defecto con ángulo grande (~80-100°) → **L**.
   - Si no, y hay 1 defecto con ángulo pequeño (<40°) y dedos paralelos → **H**.
   - Si nada encaja con suficiente margen → **ninguna/desconocida** (mejor no forzar una clasificación dudosa).
2. Implementarlo como una función pura `classify(features) -> str` fácil de testear unitariamente con los vectores del Paso 5.
3. Añadir una pequeña "zona muerta" (umbral con margen) alrededor de cada frontera de decisión para evitar que el sistema parpadee entre dos letras cuando el valor está justo en el límite.
4. Documentar en el propio código (comentario) la justificación de cada umbral — se reutiliza casi literal en el informe.

## Qué necesita estar hecho antes
Paso 5, y preferiblemente haber corrido `extract_features` sobre las ~15-20 imágenes por clase del Paso 2 para tener números reales, no solo intuición.

## Entregable del paso
Función `classify(features: dict) -> str` en `lse_auth/classifier.py`, con un pequeño test manual que recorre el dataset de referencia y muestra una matriz de confusión simple (aciertos por clase).

## Primera versión (21/11): H, O y L
Solo H, O y L, que son las letras con fotos válidas (A y NONE están pendientes de repetir). Cualquier otra cosa devuelve `None`: para el decodificador es mejor perder un frame que aceptar una letra equivocada.

### Por qué no ángulos absolutos ni tamaños absolutos
La primera versión miraba hacia dónde apuntaba cada dedo (p. ej. "la L tiene un dedo a 70–115°"). Con las fotos de Tere iba perfecta, pero en directo con la mano de Claudia su **O se leía como H** y la **H con los dedos pegados no se reconocía**. La segunda versión usaba anchuras absolutas (≥ 0,85 radios = dos dedos), y la H pegada de Claudia (0,80–0,83) se leía como **L**. Una tercera comparaba la anchura del dedo con la del pulgar de la misma mano, pero **el pulgar visto de lado mide solo 0,23–0,25** y entonces un índice normal parecía dos dedos: la **L se leía como H**. Cada persona gira la muñeca distinto, así que las reglas se apoyan en lo que es estable: la estructura (pulgar sí/no, cuántas puntas) y la anchura de los dedos en radios de palma, con la dirección solo para desempatar.

### Reglas (versión 4)
1. **Pulgar**: el último dedo (el de mayor ángulo: con la mano derecha en espejo queda a la izquierda) si está separado de su vecino **50–130°** y es **fino** (≤ 0,8 radios). Con el pulgar estirado el hueco pulgar-índice siempre es amplio; los demás dedos están mucho más juntos. Si hay agujero de O, ese "dedo" es el círculo y no el pulgar.
   - **Pulgar levantado (22/11)**: con el índice y el pulgar los dos hacia arriba, el hueco baja a ~46° y la H se leía como **O** (tres puntas sin pulgar). Ahora también basta un hueco de **35–50°** si esa punta es claramente **más corta** que su vecina (≤ 0,9 de su longitud). El pulgar mide 0,63–0,85 del índice; en la O la punta de la izquierda es el dedo corazón, el más largo (0,99–1,18 de su vecino), así que no se confunden.
2. Los demás dedos se cuentan. Dos dedos pegados dan una sola punta: se distinguen por la **anchura** (radios de palma): ≤ 0,65 un dedo (medido 0,45–0,60), ≥ 0,75 dos dedos (medido 0,79–0,92). Entre medias decide la dirección: la H apunta al lado (< 70°), la L hacia arriba.

| Letra | Regla | Medido |
|---|---|---|
| L | pulgar + 1 dedo fino | índice 0,45–0,60 a 92–114° |
| H | pulgar + 1 dedo ancho (dos pegados), **o** pulgar + 2 dedos a < 45° entre sí y hacia el lado | pegados 0,79–0,92 a 36–40°; separados ~20° y ~45° |
| O | **sin pulgar** + 3 puntas, **o** sin pulgar + 2 puntas con una ≥ 1,6 × la otra, **o** agujero de O + ≥ 2 puntas | — |

- La O necesita al menos un dedo fino: los bultos de un puño no son dedos.
- No se exige el agujero de la O: de frente, el círculo no se ve.
- Si la mano se sale del recuadro por arriba o por los lados (`cut`), no se decide nada: con un dedo cortado una H parece una L.

### Resultados
Dataset de Tere + 18 frames de Claudia guardados con `e` (con la letra que estaba haciendo):

| Real \ Predicha | H | O | L | ninguna |
|---|---|---|---|---|
| H Tere (20) | **18** | 0 | 0 | 2 |
| O Tere (15) | 0 | **15** | 0 | 0 |
| L Tere (19) | 0 | 0 | **19** | 0 |
| H Claudia (8) | **8** | 0 | 0 | 0 |
| O Claudia (5) | 0 | **5** | 0 | 0 |
| L Claudia (5) | 0 | 0 | **5** | 0 |
| A (20)* | 0 | 0 | 0 | 20 |
| NONE (15)* | 0 | 0 | 0 | 15 |

\* A y NONE tienen la cámara movida respecto al fondo: sirven para comprobar que no hay falsos positivos (y de hecho sacaron varios casos que hubo que corregir: el zócalo pegado a la mano, los nudillos de un puño).

Las dos H de Tere que fallan tienen los dedos fuera del recuadro: devuelven "ninguna", no una letra equivocada.

Casos sintéticos (máscaras dibujadas, con palma de 50 y de 80 px): H pegada, H separada, H muy junta, L, O de frente, O con agujero → correctos; mano abierta, puño, "V" hacia arriba e índice solo → ninguna letra.

**Ojo**: con solo 18 frames de Claudia los umbrales pueden estar ajustados a su mano; hace falta probarlo con más gente. El margen entre "un dedo" (≤ 0,60) y "dos pegados" (≥ 0,79) es estrecho.

**El fondo importa**: con la mano delante del **corcho** (color piel y brillo parecido) la resta de fondo pierde trozos de dedos (frame 150608: un dedo de la O desaparece). Subir el peso de Y o bajar el umbral recupera el dedo pero rompe muchas otras imágenes (probado: errores de 2 a 14–63). Para la demo, mejor que detrás del recuadro haya pared lisa.

## Segunda versión (23/11): la A y una O más estricta
Con las fotos válidas de A y NONE (las de Claudia, `bg_06`: pared lisa, brazo desde abajo) se añade la A. Además, las NONE sacaron un problema serio: **9 de 25 gestos que no son letras daban O o H**.

### Por qué fallaba la O
Una mano abierta con la **palma hacia la cámara** tiene el pulgar al otro lado (a la derecha en la imagen en espejo), así que no se detecta como pulgar. Si además dos dedos salen pegados o movidos, quedan 2–3 puntas sin pulgar, y eso era justo la regla de la O. La diferencia está en **lo juntas que están las puntas**:

| | 2 puntas (separación) | 3 puntas (de la primera a la última) |
|---|---|---|
| O sin agujero (Claudia) | 20° | 30° |
| NONE que daban O | 39–41° | 45–134° |

### Reglas nuevas
| Letra | Regla | Medido |
|---|---|---|
| O | agujero de O + ≥ 2 puntas, **o** sin pulgar + 3 puntas en **≤ 38°**, **o** sin pulgar + 2 puntas a **≤ 30°** con una ≥ 1,6 × la otra | O de Tere: con agujero; O de Claudia: 30° / 20° |
| H | igual que antes, pero si los dos dedos están separados, **los dos deben ser finos** (≤ 0,8). Si están a ≤ 15° son la pareja pegada vista como dos bultos y valen aunque sean anchos | NONE 76: dedos a 20°, uno de 1,19 (tres dedos + pulgar, mano abierta) |
| A | **ningún dedo**, sin agujero de O, solidez **≥ 0,75** y `top_extent` **≤ 1,55** | puño: solidez 0,78–0,85, `top_extent` 1,22–1,51; mano abierta sin puntas: 1,58–1,70 |

El `top_extent` (Paso 5) distingue el puño de una mano abierta en la que no se detectan las puntas. Pasa con los dedos pegados o con la mano movida al saludar (NONE 64 y 67, y un frame movido de `errores/` que daba A con 1,58).

### Resultados (23/11)
| Real \ Predicha | H | O | L | A | ninguna |
|---|---|---|---|---|---|
| H Tere (20) | **18** | 0 | 0 | 0 | 2 |
| O Tere (15) | 0 | **15** | 0 | 0 | 0 |
| L Tere (19) | 0 | 0 | **19** | 0 | 0 |
| H Claudia (8) | **8** | 0 | 0 | 0 | 0 |
| O Claudia (5) | 0 | **5** | 0 | 0 | 0 |
| L Claudia (5) | 0 | 0 | **5** | 0 | 0 |
| A Claudia (20) | 0 | 0 | 0 | **20** | 0 |
| NONE Claudia (25)¹ | 0 | 0 | 0 | 0 | **25** |
| NONE Tere (17)² | 0 | 0 | 0 | 0 | 17 |
| A Tere (12)² | 1 | 1 | 0 | 0 | 10 |

¹ 5 con el recuadro vacío, el resto con gestos que no son letras (mano abierta, la V, tres dedos, saludo movido…). Antes de los cambios: 8 daban O y 1 daba H.

² Las de Tere (`bg_02`, `bg_03`) tienen **marcos dorados dentro del recuadro**, que salen como piel cuando la cámara cambia la exposición. En las A además el **brazo entra de lado, en horizontal**, y la mano está pegada a la cámara. Casi todas acaban como "mano cortada" (`cut`). Dos de esas A de lado dan H y O: los dedos del puño visto de canto parecen puntas. No se ha ajustado nada para ellas. Las letras se hacen con el brazo desde abajo, como en el resto del dataset.

**Ojo**:
- La A y la NONE son de **una sola persona (Claudia)**, y los márgenes son estrechos: `top_extent` 1,51 frente a 1,58, y en la O 30° frente a 45°.
- La O de frente sin agujero solo tiene 3 frames medidos.
- Antes de la demo hay que probarlo en directo con las dos manos y guardar con `e` lo que falle.

### En directo
- **Suavizado**: en pantalla solo se muestra una letra si gana la mayoría (≥ 60 %) de los últimos 9 frames, para que un frame malo no la cambie (primera versión del Paso 7).
- **Depurar**: la tecla **`e`** guarda frame + fondo en `errores/` (no se sube a git: salen caras y habitaciones) y `python -m lse_auth.segmentation_preview --errors` los vuelve a procesar, imprime ángulo, anchura y longitud de cada dedo y guarda `*_result.jpg`.

Código: `lse_auth/classifier.py` → `classify(features) -> "H" | "O" | "L" | "A" | None`.
