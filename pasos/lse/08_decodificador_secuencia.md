# Paso 8 — Decodificador de secuencia (memoria de 4 patrones + bloqueo/desbloqueo)

## Rama
`feature/sign-language-auth`

## Descripción
Este es el requisito explícito del guion: "implementar un decodificador que memorice hasta 4 patrones consecutivos y garantice o bloquee el paso al siguiente bloque en función de si estos patrones están en el orden correcto o no", con lógica para resetear/olvidar la secuencia cuando haga falta. Aquí la secuencia objetivo es fija: **H → O → L → A**.

## Cómo hacerlo
1. Mantener un buffer de letras confirmadas (lista, máx. 4 elementos) y la secuencia objetivo `["H", "O", "L", "A"]`.
2. Cada vez que `StableLetterDetector` (Paso 7) confirma una letra:
   - Si coincide con la posición esperada del buffer (siguiente letra de la secuencia objetivo), añadirla al buffer.
   - Si NO coincide, **resetear el buffer a vacío** (no simplemente seguir acumulando) — así un error obliga a empezar de nuevo, tal como pide el guion.
3. Cuando el buffer llega a longitud 4 y coincide exactamente con `H-O-L-A` → emitir evento `unlock_granted()` / cambiar a estado `DESBLOQUEADO`.
4. Añadir un timeout razonable (p. ej. 20-30 s sin completar la secuencia) que resetee el buffer automáticamente, para que el sistema no se quede "a medias" indefinidamente si el usuario se distrae.
5. Guardar también un pequeño log en consola de cada transición (útil para depurar y para capturas del informe/vídeo).

## Qué necesita estar hecho antes
Paso 7 (`StableLetterDetector` devolviendo letras confirmadas, no clasificación ruidosa frame a frame).

## Entregable del paso
Clase `SequenceDecoder` en `lse_auth/sequence_decoder.py` con métodos `feed(letter)`, `is_unlocked()`, `reset()`, y estado interno expuesto para la UI del Paso 9.

## Implementación (22/11)
`lse_auth/sequence_decoder.py`, clase `SequenceDecoder`. Parámetros en `config.py` (bloque "Sequence decoder"): `UNLOCK_SEQUENCE = ("H", "O", "L", "A")` y `SEQUENCE_TIMEOUT = 30` s.

Recibe las letras **ya confirmadas** por el `StableLetterDetector` del Paso 7, que da una por seña y no una por frame. Así el decodificador no tiene que preocuparse del ruido.

### Reglas
| Situación | Evento | Buffer después |
|---|---|---|
| La letra es la siguiente esperada | `CORRECT` | se añade (`H-O-_-_`) |
| Con ella se completa el código | `UNLOCKED` | `H-O-L-A`, queda desbloqueado |
| Letra equivocada | `WRONG` | vacío: hay que empezar de nuevo |
| Letra equivocada pero es la **primera** del código (H) | `RESTART` | `H-_-_-_` |
| Pasan 30 s sin ninguna letra correcta | `TIMEOUT` | vacío |
| `reset()` desde fuera | `RESET` | vacío y bloqueado |

- **Un error obliga a empezar de cero**, como pide el guion: el buffer no "sigue acumulando" después de un fallo.
- **`RESTART`**: si alguien hace H-O y se equivoca volviendo a hacer H, lo natural es que esa H sea el primer paso del nuevo intento. Si se vaciara el buffer, tendría que sacar la mano y repetir la H (el Paso 7 no confirma la misma letra dos veces sin hueco).
- **Timeout**: cuenta desde la última letra correcta, así que no hay que hacer las cuatro letras en 30 s, sino no estar más de 30 s parado entre una y otra. Se comprueba en `feed()` y también en `tick()`, que el bucle llama en cada frame: así salta aunque no se vea ninguna letra (la persona se ha ido). 30 s es el máximo que proponía el plan (20–30 s); se eligió el máximo para dejar margen entre letras a quien no está acostumbrado a deletrear en LSE. Una letra confirmada tarda ~0,5 s, así que sobra tiempo para colocar la mano.
- **Una vez desbloqueado** se ignoran las letras hasta `reset()`: lo que pase después lo decide el bloque del tracker (Paso 10).
- Cada transición se imprime (`[decoder] correct O -> H-O-_-_`) y se guarda en `events`, con el tiempo, el evento y la letra, para depurar y para las capturas del informe.

### Estado para la interfaz (Paso 9)
`is_unlocked()`, `expected` (siguiente letra), `progress_text` (`"H-O-_-_"`), `last_event` (para mostrar "Secuencia incorrecta" unos segundos) y `time_left()` (segundos hasta que se olvide la secuencia).

### La A todavía no se reconoce
Hasta que estén las fotos nuevas de la A (issue #6), con H-O-L-A no se puede desbloquear. Para probar el flujo completo en directo, el preview acepta un código distinto:

```
python -m lse_auth.segmentation_preview --code HOL
```

En el preview, abajo sale el progreso (`H-O-_`) y, cuando se completa, "DESBLOQUEADO". Con un error se muestra "Secuencia incorrecta" 2 s, y con el timeout, "Tiempo agotado". `r` vuelve a bloquear y vacía todo.

### Pruebas
`python -m pytest tests/test_sequence_decoder.py`: 9 tests y pasan todos.
- H-O-L-A desbloquea.
- Un error vacía el buffer y después H-O-L-A desbloquea.
- O-H-L-A y H-L-O-A no desbloquean.
- H-O-H reinicia en `H-_-_-_`.
- El timeout borra una secuencia empezada, también con una letra que llega tarde.
- Con 15 s entre letras (45 s en total) sigue desbloqueando.
- Desbloqueado se ignoran las letras hasta `reset()`.
- El código corto `HOL` funciona.
- Los eventos quedan registrados.
