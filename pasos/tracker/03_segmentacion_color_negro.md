# Paso 3 — Segmentación por color (zapato negro)

## Rama
`feature/rope-jump-counter`

## Descripción
Separar el zapato negro del resto de la imagen frame a frame. El negro es un color complicado de segmentar por tono (hue), porque a baja saturación el hue es poco fiable — hay que basarse sobre todo en luminosidad (value) baja, y tener cuidado con confundir el zapato con sombras del suelo, pelo oscuro o ropa oscura.

## Cómo hacerlo
1. Convertir el frame (ya corregido de distorsión) a HSV con `cv2.cvtColor`.
2. Umbralizar por **value bajo** (p. ej. `V < 60-80`, a ajustar) y opcionalmente **saturación baja-media**, con `cv2.inRange`. No hace falta acotar mucho el hue para negro.
3. Aplicar morfología (`MORPH_OPEN` para quitar ruido suelto, `MORPH_CLOSE` para rellenar el zapato si queda con agujeritos por brillos/reflejos en el cuero).
4. Definir una ROI vertical amplia (toda la franja donde se mueve el pie al saltar, no solo el suelo) para no perder el zapato en el punto más alto del salto, pero sí descartar zonas donde nunca va a estar (p. ej. la mitad superior de la imagen si la cámara encuadra cuerpo entero).
5. Si hay sombra proyectada por el propio salto, probar a normalizar iluminación (ecualización de histograma en V) antes de umbralizar, o simplemente pedir un fondo claro y una superficie que no genere sombras duras — más simple y suficiente para el proyecto.

## Qué necesita estar hecho antes
Paso 2 (vídeos de referencia para ajustar umbrales) y la corrección de distorsión de la calibración ya aplicada al frame.

## Entregable del paso
Función `segment_shoe(frame) -> mask` en un nuevo paquete, p. ej. `jump_tracker/segmentation.py` (ver Paso 13 sobre por qué un paquete propio y no meterlo dentro de `lse_auth/`).
