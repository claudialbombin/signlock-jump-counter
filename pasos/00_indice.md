# Índice — Bloque "Desbloqueo por LSE (H-O-L-A)"

División del trabajo de Claudia (Sistema de Seguridad: detección de patrones + decodificador de secuencia), en 12 pasos. Rama de trabajo principal: `feature/sign-language-auth`.

| # | Paso | Depende de |
|---|------|------------|
| 1 | Definición del alfabeto LSE objetivo (H-O-L-A) | — |
| 2 | Captura del set de imágenes de referencia | 1, `feature/calibration` (en `main`) |
| 3 | Segmentación de piel / aislamiento de la mano | 2 |
| 4 | Detección del contorno de la mano | 3 |
| 5 | Extracción de características geométricas | 4 |
| 6 | Clasificador por reglas (H/O/L/A/ninguna) | 5 |
| 7 | Estabilización temporal de la detección | 6 |
| 8 | Decodificador de secuencia (memoria 4 letras + bloqueo/reset) | 7 |
| 9 | Feedback visual en pantalla | 8, 4 |
| 10 | Integración con el bloque siguiente (tracker) | 8, 9 → `feature/integration` |
| 11 | Pruebas, ajuste de umbrales y medición de robustez | 3–9 |
| 12 | Documentación para informe y vídeo | 1–11 |

Notas generales:
- Todo el desarrollo de este bloque vive en `feature/sign-language-auth` y se integra al final con el resto vía `feature/integration` (Paso 10), igual que `feature/calibration` ya se mergeó en `main`.
- La calibración de cámara (rama `feature/calibration`, ya en `main`) es prerequisito transversal: los frames que entran al Paso 3 deben pasar antes por `cv2.undistort` con los parámetros ya calculados.
- Es visión clásica de principio a fin (sin deep learning), en línea con lo que pide el guion del proyecto.
