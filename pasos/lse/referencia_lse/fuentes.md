# Fuentes de las imágenes de referencia (H-O-L-A)

Imágenes de referencia visual para las 4 letras del alfabeto dactilológico LSE usadas en el
desbloqueo del proyecto. Son solo material de apoyo interno (no se entregan como tal), recortadas
de capturas de pantalla de búsquedas web.

- `letra_A_signame.png`, `letra_H_signame.png`, `letra_L_signame.png`, `00_grid_A-M_signame.jpg`:
  recortadas de la ilustración del alfabeto dactilológico LSE de Sígname —
  https://signame.es/alfabeto-dactilologico-lse/
- `letra_O_foaps.png`: recortada de una foto real de mano en una página de Foaps sobre el
  alfabeto manual/dactilológico (resultado de imágenes de Google, blog Foaps).

## Lo que confirman (para los Pasos 1, 5 y 6 de `pasos/`)

- **A**: puño cerrado, pulgar visible apoyado al lateral de los dedos. Sin dedos sueltos.
- **H**: índice y corazón extendidos y juntos (como una "V" cerrada), con un pequeño símbolo de
  movimiento junto a la mano en la ilustración (sugiere una ligera rotación de muñeca — a validar
  en vuestra propia versión estática).
- **L**: índice extendido hacia arriba, pulgar extendido en ángulo recto hacia el lateral. Forma
  de "L" clara.
- **O**: pulgar e índice se tocan formando un círculo pequeño (como el signo "OK"), el resto de
  dedos (corazón, anular, meñique) quedan extendidos hacia arriba. OJO: esto es distinto a lo que
  se apuntó inicialmente en el Paso 1 ("todas las yemas tocando el pulgar") — el agujero real es
  solo entre pulgar e índice, y hay 3 dedos sueltos extendidos. Hay que actualizar el Paso 1 y,
  sobre todo, el Paso 5/6: el contorno de la O va a tener TANTO un hueco interior (pulgar-índice)
  COMO 2-3 dedos extendidos detectables por convexity defects — no basta con mirar "has_hole" a
  secas, hay que combinarlo con el conteo de dedos para no confundirla con una mano relajada.
