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
