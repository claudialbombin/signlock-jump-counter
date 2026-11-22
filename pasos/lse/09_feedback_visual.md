# Paso 9 — Feedback visual en pantalla

## Rama
`feature/sign-language-auth`

## Descripción
El usuario necesita ver en tiempo real qué está pasando: qué letra se está detectando ahora mismo, cuánto lleva de la secuencia H-O-L-A, y si está bloqueado o desbloqueado. Esto también es lo que luego se graba para el vídeo-demo del entregable.

## Cómo hacerlo
1. Sobre el frame de salida, dibujar con `cv2.putText`/`cv2.rectangle`:
   - El bounding box y el contorno de la mano (reutilizando el Paso 4), en un color si está "reconociendo" y en otro si ya ha confirmado letra.
   - La letra detectada en el frame actual (aunque no esté aún confirmada), p. ej. en pequeño y gris.
   - El progreso de la secuencia como texto tipo `H-O-_-_ ` (usar el estado de `SequenceDecoder`).
   - Un mensaje grande de estado: `BLOQUEADO` (rojo) / `DESBLOQUEADO` (verde), ocupando una esquina fija de la pantalla.
2. Si se resetea la secuencia por error, mostrar brevemente un mensaje tipo "Secuencia incorrecta, inténtalo de nuevo" (2-3 segundos) antes de volver al estado normal.
3. Mantenerlo ligero (nada de overlays pesados) para no comprometer la tasa de refresco — el guion valora explícitamente que no se vea afectada.

## Qué necesita estar hecho antes
Paso 8 (`SequenceDecoder` con estado consultable) y Paso 4 (contorno/bbox para dibujar).

## Entregable del paso
Función `draw_overlay(frame, contour, bbox, current_letter, decoder_state) -> frame` en `lse_auth/overlay.py`.

## Implementación (22/11)
`lse_auth/overlay.py`, función `draw_overlay(view, hand, letter, detector, decoder, cut=False, now=None) -> view`.

La firma cambia un poco respecto al plan:
- recibe el `HandContour` del Paso 4, que ya lleva el contorno y el bbox;
- recibe el `StableLetterDetector` del Paso 7, para la barra de confirmación y el color del contorno;
- recibe el `SequenceDecoder` entero del Paso 8, que es el "estado del decodificador".

### Qué se ve
| Zona | Qué | Colores |
|---|---|---|
| Esquina superior izquierda | Cartel **BLOQUEADO** / **DESBLOQUEADO** | rojo / verde |
| Debajo | Una casilla por letra del código. Las hechas llevan la letra; la siguiente está resaltada. Debajo, los segundos que quedan antes de que se olvide la secuencia (Paso 8, 30 s). | hechas en verde, siguiente en amarillo, resto en gris |
| Recuadro de la mano (ROI) | Contorno y bbox de la mano | naranja mientras se reconoce, verde cuando la letra está confirmada; el recuadro se pone verde al desbloquear |
| A la derecha del recuadro | Letra del frame actual, pequeña, y una barra que se llena mientras el Paso 7 la confirma | gris; verde cuando está confirmada |
| Abajo en el centro, 2,5 s | "Secuencia incorrecta, intentalo de nuevo" / "Tiempo agotado, empieza de nuevo" | rojo |
| Encima del recuadro | "Mete toda la mano en el recuadro" si la mano se sale | rojo |

### Decisiones
- **Las casillas pendientes no muestran la letra.** El código es una contraseña: si la pantalla dijera "siguiente: L", cualquiera que mire podría desbloquear. Solo se ve cuántas letras tiene y cuántas llevas.
- **La letra del frame va pequeña y en gris** hasta que se confirma. Así se distingue "lo que el sistema cree ver ahora" de "lo que ha contado". La barra hace visible el medio segundo de espera del Paso 7, que si no parecería que el sistema no responde.
- **Mensaje de error 2,5 s** (el plan pedía 2–3 s). Va abajo en el centro para no tapar la mano ni el cartel.
- **Textos sin tildes**: `cv2.putText` solo tiene fuentes ASCII ("intentalo" en vez de "inténtalo").
- **Coste**: unos rectángulos, un contorno y algo de texto. Medido en 1280×720: **~1,4 ms por frame**, frente a los ~15 ms del resto del procesado, así que no baja la tasa de refresco. `tests/test_overlay.py` comprueba que se queda por debajo de 5 ms.

### Preview
`python -m lse_auth.segmentation_preview` (o con `--code HOL` mientras no esté la A) dibuja siempre el overlay del Paso 9. Por encima va una capa de depuración:
- la máscara pintada de verde;
- la palma, las puntas y las anchuras;
- el número de dedos.

La tecla **`d`** muestra u oculta la capa de depuración: sin ella queda la vista limpia para grabar el vídeo. La lista "Confirmadas" del Paso 7 desaparece, porque ya la sustituyen las casillas.

### Pruebas
`python -m pytest tests/test_overlay.py`: 3 tests con un frame y una mano sintéticos, y pasan todos.
- Se dibujan sin errores todos los estados: recuadro vacío, letra confirmándose, mano cortada, letra confirmada, código a medias, error y desbloqueado.
- El mensaje de error desaparece pasados los 2,5 s.
- El coste queda por debajo de 5 ms por frame.

Además se ha comprobado a ojo sobre frames reales guardados con `e`: confirmando una H, con H-O hecho y con la capa de depuración, tras un error y desbloqueado con `HOL`. Falta verlo en directo con la cámara.
