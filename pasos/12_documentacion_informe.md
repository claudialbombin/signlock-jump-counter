# Paso 12 — Documentación para el informe y el vídeo

## Rama
`feature/sign-language-auth` → contenido final se incorpora en `main` (vía PR normal, igual que hizo `feature/calibration`)

## Descripción
Dejar redactada y lista tu parte del informe final (máx. 5 páginas en total, compartido con el resto del equipo) y preparado el material visual que se usará en el vídeo-demo. El guion pide explícitamente, dentro de "Metodología": diagrama de bloques, secuencia de transformación de la imagen, y "Sistema de seguridad: Detección de patrones y Extracción de información" — es justo tu bloque.

## Cómo hacerlo
1. Escribir un bloque de texto (para que el compañero/a que compile el informe final lo inserte) que cubra:
   - Qué es LSE dactilológica y por qué se eligió H-O-L-A como patrón (referencia bibliográfica mínima sobre LSE y sobre las técnicas clásicas usadas: segmentación por color de piel, convex hull/convexity defects — el guion pide justificar con bibliografía).
   - Explicación del pipeline: segmentación → contorno → características → clasificador por reglas → estabilización temporal → decodificador de secuencia.
   - Resultados del Paso 11 (tabla de aciertos/fallos).
   - Limitaciones y futuros desarrollos (p. ej. aceptar ambas manos, más letras, adaptación automática de umbrales de piel).
2. Preparar 1 figura tipo "secuencia de transformación de la imagen" específica de tu bloque: frame original → máscara de piel → contorno+hull dibujado → overlay final con letra/estado (reutilizando capturas ya generadas en pasos anteriores).
3. Grabar un clip corto (10-20 s) mostrando el deletreo completo H-O-L-A y el cambio a "DESBLOQUEADO", con el overlay de FPS visible (requisito del vídeo final: "debe incrustar en sus frames la tasa de refresco a la que se ejecuta el sistema").
4. Indicar explícitamente, como pide el guion, qué asistentes de IA se han usado y para qué (en este caso, para planificar y repartir estos pasos).

## Qué necesita estar hecho antes
Pasos 1 a 11 completos; idealmente también el Paso 10 (integración) para poder grabar el flujo completo seguridad → tracker en el mismo clip.

## Entregable del paso
Texto Markdown con tu sección del informe (en `pasos/informe_bloque_seguridad.md`), figura de secuencia de transformación, y clip de vídeo de tu bloque.
