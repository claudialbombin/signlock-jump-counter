# Paso 7 — Estabilización temporal de la detección

## Rama
`feature/sign-language-auth`

## Descripción
Frame a frame, la clasificación del Paso 6 va a "parpadear" (ruido, ligero movimiento de mano, frame suelto mal segmentado). Antes de pasarle nada al decodificador de secuencia (Paso 8), hay que exigir que una letra se mantenga detectada de forma consistente durante varios frames seguidos para darla por válida. Esto también ayuda a que el usuario tenga tiempo de "mostrar" cada letra y pasar a la siguiente de forma natural.

## Cómo hacerlo
1. Mantener un pequeño buffer/cola con las últimas `N` clasificaciones (p. ej. `N = 10-15` frames, ajustar según FPS real).
2. Si las últimas `N` clasificaciones son todas la misma letra (o al menos un `% ` alto, p. ej. 80%), considerarla "confirmada" y emitirla una sola vez al decodificador (no repetidamente mientras se mantiene la mano).
3. Tras confirmar una letra, exigir ver la clase "ninguna" (mano retirada o cambiada) durante un par de frames antes de poder confirmar la siguiente letra — evita que una sola seña sostenida cuente como "H, H, H..." y rompa la lógica de 4 letras del Paso 8.
4. Exponer esto como una máquina de estados pequeña: `ESPERANDO_SEÑA → CONFIRMANDO → CONFIRMADA → ESPERANDO_RESET`.

## Qué necesita estar hecho antes
Paso 6 (`classify` funcionando frame a frame).

## Entregable del paso
Clase/función `StableLetterDetector` en `lse_auth/stabilizer.py` con un método `update(mask_classification) -> Optional[str]` que devuelve la letra solo cuando se confirma, y `None` el resto del tiempo.

## Implementación (22/11)
`lse_auth/stabilizer.py`, clase `StableLetterDetector`. Parámetros en `config.py` (bloque "Temporal stabilisation").

### Máquina de estados
```
WAITING ──(aparece una letra)──▶ CONFIRMING ──(0,5 s y ≥ 80 % de frames)──▶ CONFIRMED
   ▲                                  │ (otra letra gana → vuelve a empezar)       │
   │                                  ▼                                            ▼
   └──────(la letra confirmada lleva 0,3 s sin verse)────────────────── WAITING_RESET
```
- `update(letter, now=None)` recibe la letra del frame (`"H"`, `"O"`, `"L"` o `None`) y devuelve la letra **solo en el frame en que se confirma**; el resto del tiempo devuelve `None`.
- Se guarda una ventana con las clasificaciones de los últimos `STABLE_CONFIRM_TIME` segundos. Una letra se confirma cuando lleva ese tiempo siendo la más frecuente de la ventana, ocupa al menos `STABLE_MIN_SHARE` de los frames y la ventana tiene al menos `STABLE_MIN_FRAMES` frames.
- Después de confirmar, mientras se siga viendo la misma letra no se emite nada (mantener la H diez segundos da **una** H). Cuando la letra confirmada lleva `STABLE_RESET_TIME` sin verse (mano fuera, ninguna letra **u otra letra**), se rearma.
- `progress` (0–1) y `state` se exponen para la interfaz (barra de progreso en el preview y, más adelante, el Paso 9).

### Decisiones
| Parámetro | Valor | Por qué |
|---|---|---|
| `STABLE_CONFIRM_TIME` | 0,5 s | ≈ 15 frames a 30 fps, lo que proponía el plan (10–15). En segundos y no en frames porque el preview va a 15–30 fps según el portátil. Medio segundo es lo bastante corto para que no se haga pesado y lo bastante largo para que la transición entre dos letras (unos pocos frames con letras sueltas) no se confirme. |
| `STABLE_MIN_SHARE` | 0,8 | Tolera algún frame suelto mal clasificado (uno de cada cinco), pero no un parpadeo H/L constante. |
| `STABLE_MIN_FRAMES` | 6 | Si el portátil va muy lento no se confirma con 2–3 frames. |
| `STABLE_RESET_TIME` | 0,3 s | Un par de frames perdidos (mano que se mueve, máscara mala) no cuentan como "retirar la mano" y no repiten la letra; sacar la mano de verdad dura bastante más. |

- **"Otra letra" también rearma.** El plan pedía ver "ninguna" antes de la siguiente letra. Al pasar de H a O sin sacar la mano lo normal es que el clasificador dé `None` unos frames en medio (posturas intermedias), pero no está garantizado: si se exigiera `None` explícito, la O se podría perder. Ahora la O hace que la H "desaparezca", el detector se rearma y la O se confirma con su medio segundo normal.
- **La misma letra dos veces seguidas necesita un hueco.** Para H-O-L-A no pasa nunca, pero si el usuario se equivoca y repite la letra, el decodificador del Paso 8 lo verá como una sola.
- Al rearmarse se borran de la ventana los frames de la letra anterior, para que no "ayuden" a confirmarla otra vez.
- El `LetterSmoother` del preview (voto por mayoría de 9 frames) se queda solo para que la letra en pantalla no parpadee; las letras que cuentan son las del detector.

### Preview
`python -m lse_auth.segmentation_preview`:
- Debajo de la letra aparece una barra que se llena mientras se confirma. Cuando la letra está confirmada se lee "H ok - cambia de letra".
- Abajo se lista "Confirmadas: H O L". Al confirmar una letra la lista se pone en verde medio segundo y la letra se escribe en consola (`[stabilizer] confirmed H -> H`).
- `r` borra la lista. `f` (nuevo fondo) también reinicia el detector.

### Pruebas
`python -m pytest tests/test_stabilizer.py`: 10 tests con secuencias sintéticas de letras a 30 fps (y una a 15 fps). Todos pasan.

| Caso | Resultado esperado |
|---|---|
| H mantenida 10 s | `["H"]` (una sola) |
| H de 0,3 s | nada |
| H, O, L sacando la mano entre letras | `["H", "O", "L"]` |
| H → O → L sin sacar la mano | `["H", "O", "L"]` |
| O, O sin hueco / con 0,5 s fuera | `["O"]` / `["O", "O"]` |
| L con un 10 % de frames erróneos al azar | `["L"]` |
| Parpadeo H/L frame a frame | nada |
| H con 2 frames perdidos en medio | `["H"]` (no se repite) |
| O a 15 fps | `["O"]` |

Falta probarlo en directo con las dos manos. Si al usarlo se hace lento o salta letras, los cuatro parámetros están en `config.py`.
