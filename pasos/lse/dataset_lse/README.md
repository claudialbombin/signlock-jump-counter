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

- `0`–`4` elige la clase, `c` o espacio captura, `b` hace una ráfaga de 5 fotos, `d` borra la última, `q` sale.
- Mano **derecha** dentro del recuadro verde, ~15–20 imágenes por clase, variando un poco la posición y, si se puede, la luz.
- Para `NONE` conviene variar: mano abierta, puño con el pulgar delante, fondo sin mano, cara dentro del encuadre…

Comprobar el resultado:

```bash
python -m lse_auth.capture_dataset --summary   # cuenta por clase + overview.jpg
```

## Formato

`<clase>/img_XX.jpg`, JPEG calidad 95 (un PNG de 1280x720 ocupa ~10 veces más y haría el repo muy pesado; para segmentar piel no hay diferencia apreciable).
