# Índice — Bloque "Contador de saltos por tracking de zapato negro"

División del trabajo del "Sistema Propuesto" (tracker + ampliaciones), en 15 pasos. Rama de trabajo principal: `feature/rope-jump-counter`.

| # | Paso | Depende de |
|---|------|------------|
| 1 | Definición del objetivo: qué cuenta como "salto" | — |
| 2 | Captura de vídeo de referencia | 1, `feature/calibration` (en `main`) |
| 3 | Segmentación por color (zapato negro) | 2 |
| 4 | Detección del blob del zapato y filtrado por forma | 3 |
| 5 | Elección e inicialización del tracker | 4 |
| 6 | Bucle de seguimiento frame a frame | 5 |
| 7 | Extracción de la señal de posición vertical | 6 |
| 8 | Suavizado de la señal | 7 |
| 9 | Detección de picos (saltos) | 8 |
| 10 | Lógica de conteo en tiempo real | 9 |
| 11 | Feedback visual en pantalla | 10, 6 |
| 12 | Integración con el bloque de seguridad (LSE) | 11 → `feature/integration` |
| 13 | Reutilizar infraestructura compartida (cámara/calibración) | coordinación transversal, resolver pronto |
| 14 | Pruebas, ajuste de umbrales y medición de precisión | 3–11 |
| 15 | Documentación para informe y vídeo | 1–14 |

## Notas de coherencia con el otro bloque (`feature/sign-language-auth`)

- **No reimplementar la cámara/calibración.** Ya existe `lse_auth/camera.py` (clase `Camera`) y `calibration/camera_params.npz`, construidos en la rama de seguridad. Ver Paso 13 — hay que decidir juntos si se importa tal cual mientras tanto o se mueve a un paquete compartido (`core/`) pronto, para no generar dos formas distintas de leer la cámara en el mismo proyecto.
- **La interfaz de desbloqueo la define el otro bloque**, no la inventes por tu cuenta: revisa `pasos/lse/10_integracion_con_tracker.md` de `feature/sign-language-auth` antes de cerrar el Paso 12 de aquí, y poneos de acuerdo en la forma exacta (`is_unlocked`, `run_security_block(cap)`, etc.).
- **Paquete propio**: todo el código de este bloque vive en un paquete nuevo, p. ej. `jump_tracker/` (paralelo a `lse_auth/`), no dentro de `lse_auth/` — son bloques independientes del sistema hasta la integración final.
- Es visión clásica de principio a fin (sin deep learning), igual que el bloque de seguridad, en línea con lo que pide el guion.
- Todo el desarrollo vive en `feature/rope-jump-counter` y se integra al final con el resto vía `feature/integration`, igual que `feature/calibration` ya se mergeó en `main` y que `feature/sign-language-auth` se integrará cuando esté lista.
