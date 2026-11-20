# Dataset de referencia LSE (Paso 2)

Imágenes propias de cada clase, ya **corregidas de distorsión** con la calibración
(`calibration/camera_params.npz`) y **en espejo**, igual que las verá el sistema en directo.

| Carpeta | Clase | Tecla en la captura |
|---------|-------|---------------------|
| `NONE/` | ninguna seña (mano relajada, otros gestos, fondo vacío) | `0` |
| `H/` | H | `1` |
| `O/` | O | `2` |
| `L/` | L | `3` |
| `A/` | A | `4` |

## Cómo capturar

```bash
python -m lse_auth.capture_dataset
```

- **Primero el fondo**: con el recuadro vacío (sin mano ni brazo), pulsa `f`. Se promedian ~30 frames de la escena vacía y se guardan en `_background/bg_XX.jpg`. Hasta que no hay fondo, la herramienta no deja capturar.
- `0`–`4` elige la clase, `c` o espacio captura, `b` hace una ráfaga de 5 fotos, `d` borra la última, `q` sale.
- **Cámara quieta** toda la sesión. Si se mueve la cámara o cambia la luz, vacía el recuadro y vuelve a pulsar `f`.
- Mano **derecha dentro del recuadro verde**, dedos hacia arriba y **lo menos posible de brazo** dentro del recuadro. ~15–20 imágenes por clase, variando un poco la posición.
- Ayuda (no obligatorio): luz blanca y uniforme, y un fondo liso detrás de la mano.
- Para `NONE` conviene variar: mano abierta, puño con el pulgar delante, fondo sin mano, cara dentro del encuadre…

Comprobar el resultado:

```bash
python -m lse_auth.capture_dataset --summary   # cuenta por clase + overview.jpg
```

## Por qué hace falta el fondo

Con la primera tanda de fotos se vio que el color de piel por sí solo no basta: la madera de la estantería y la pared con luz cálida caen en el mismo rango Cr/Cb que la piel. El Paso 3 resta la escena vacía y solo después filtra por color de piel, así que cada imagen necesita su fondo.

## Formato

`backgrounds.csv` guarda qué fondo corresponde a cada imagen (`image,background`, rutas relativas a esta carpeta). Las imágenes antiguas sin fondo no aparecen en él.

`<clase>/img_XX.jpg`, JPEG calidad 95 (un PNG de 1280x720 ocupa ~10 veces más y haría el repo muy pesado; para segmentar piel no hay diferencia apreciable).
