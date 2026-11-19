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
