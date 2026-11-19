# Paso 1 — Definición del alfabeto LSE objetivo (H-O-L-A)

## Rama
`feature/sign-language-auth`

## Descripción
Antes de tocar código, hay que fijar con precisión qué cuatro configuraciones de mano se van a reconocer. El sistema debe desbloquear únicamente cuando se deletrea, en orden, H → O → L → A usando el alfabeto dactilológico de la Lengua de Signos Española (LSE).

Formas confirmadas con imágenes de referencia reales (ver `pasos/referencia_lse/`, fuentes y notas en `referencia_lse/fuentes.md`):

- **A**: puño cerrado, pulgar apoyado al lateral de los dedos (no por delante ni por detrás). Silueta compacta, sin dedos sueltos. (`letra_A_signame.png`)
- **H**: índice y corazón extendidos y juntos (como una "V" cerrada / dedos pegados), resto de dedos cerrados. La ilustración de referencia incluye un pequeño símbolo de movimiento (sugiere ligera rotación de muñeca) — para el proyecto conviene tratarla como una postura estática fija, sin exigir el movimiento. (`letra_H_signame.png`)
- **L**: índice extendido hacia arriba, pulgar extendido en ángulo recto (~90°) hacia el lateral. Resto de dedos cerrados. Silueta alargada con una separación clara entre pulgar e índice. (`letra_L_signame.png`)
- **O**: pulgar e índice se tocan formando un círculo pequeño (como el signo "OK"), y los otros tres dedos (corazón, anular, meñique) quedan extendidos hacia arriba, separados entre sí. **Importante** (corrige la hipótesis inicial de "mano totalmente cerrada formando un óvalo"): la O NO es un puño con un agujero grande, es un círculo pequeño pulgar-índice + 3 dedos sueltos extendidos. Esto afecta directamente al Paso 5/6: hay que combinar "tiene hueco pequeño" con "hay ~3 dedos extendidos", no basta con mirar el hueco. (`letra_O_foaps.png`)

## Cómo hacerlo
1. Repasar las imágenes ya guardadas en `pasos/referencia_lse/` (3 ilustraciones + 1 foto real + el grid completo A-M como contexto) antes de implementar el Paso 5/6.
2. Hacer tus propias fotos de referencia (tu mano, con tu cámara y buena luz) imitando estas 4 formas — son las que realmente vais a usar para ajustar umbrales, no las de internet (esas son solo para no equivocarte de forma).
3. Decidir la mano preferente (diestra/zurda) y si se van a aceptar ambas — simplifica mucho aceptar solo una orientación de cámara/mano al principio y ampliarlo después si da tiempo.
4. Como la H de referencia muestra una variante con movimiento, decidir explícitamente (y dejarlo escrito aquí) si vuestra versión es puramente estática o si queréis aprovechar ese matiz como parte de la seña — para un proyecto de visión clásica, lo más simple y robusto es la versión estática (índice + corazón juntos, quietos).

## Qué necesita estar hecho antes
Nada técnico; es el punto de partida. Sí conviene tener ya aprobado por el profesor que el "patrón visual" del bloque de seguridad va a ser LSE dactilológica (lo pide el guion del proyecto: "planteamiento y diseño... debe contar con la aprobación del profesor").

## Entregable del paso
Este propio fichero (ya actualizado) + la carpeta `pasos/referencia_lse/` con las imágenes de referencia y sus fuentes documentadas en `fuentes.md`.
