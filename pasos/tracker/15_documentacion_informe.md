# Paso 15 — Documentación para el informe y el vídeo

## Rama
`feature/rope-jump-counter` → contenido final se incorpora en `main`

## Descripción
Dejar redactada tu parte del informe final (compartido con el resto del equipo, máx. 5 páginas en total) y preparado el material visual del vídeo-demo. El guion pide, dentro de "Metodología": "Sistema propuesto: tracker, ampliaciones y salida de vídeo" — es justo tu bloque.

## Cómo hacerlo
1. Escribir un bloque de texto (para que quien compile el informe final lo inserte) que cubra:
   - Qué aplicación se eligió (contador de saltos por tracking de zapato) y por qué.
   - Explicación del pipeline: segmentación por color → detección de blob → tracking → señal de posición → suavizado → detección de picos → conteo → overlay.
   - Justificación con bibliografía mínima de las técnicas usadas (segmentación por color en HSV, detección de picos / peak finding).
   - Resultados del Paso 14 (tabla de aciertos/fallos).
   - Limitaciones y futuros desarrollos (p. ej. soportar varios colores de zapato, saltos laterales, dos personas a la vez).
2. Preparar una figura de "secuencia de transformación de la imagen" específica de tu bloque: frame original → máscara de color → contorno+bbox dibujado → overlay final con contador y FPS.
3. Grabar un clip corto mostrando una tanda de saltos con el contador subiendo en pantalla y los FPS visibles, idealmente encadenado después del desbloqueo LSE del otro bloque (mismo clip de principio a fin si ya está integrado — ver Paso 12).
4. Indicar, como pide el guion, qué asistentes de IA se han usado y para qué.

## Qué necesita estar hecho antes
Pasos 1 a 14 completos; idealmente también el Paso 12 (integración) para poder grabar el flujo completo seguridad → tracker en el mismo clip.

## Entregable del paso
Texto Markdown con tu sección del informe (`pasos/tracker/informe_bloque_tracker.md`), figura de secuencia de transformación, y clip de vídeo de tu bloque.
