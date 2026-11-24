# paso 3: mascara de la mano dentro del recuadro
#
# solo con color de piel no funcionaba (la estanteria y la pared tienen el
# mismo Cr/Cb), asi que mano = lo que cambia respecto al fondo vacio Y que
# parece piel. Ver pasos/lse/03_segmentacion_piel.md

import cv2
import numpy as np

from lse_auth import config


def _ellipse(size):
    return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (size, size))


class BackgroundModel:
    # media de los primeros frames con el recuadro vacio
    def __init__(self, n_frames=config.BG_FRAMES):
        self.n_frames = n_frames
        self.reset()

    def reset(self):
        self._sum = None
        self._count = 0
        self.image = None

    @property
    def ready(self):
        return self.image is not None

    def add(self, frame):
        if self.ready:
            return True
        if self._sum is None:
            self._sum = np.zeros(frame.shape, np.float32)
        self._sum += frame
        self._count += 1
        if self._count >= self.n_frames:
            self.image = (self._sum / self._count).round().astype(np.uint8)
            self._sum = None
        return self.ready


def match_brightness(background, frame, bin_size=8, step=8, min_pixels=50):
    # la webcam cambia la exposicion sola cuando entra la mano, asi que
    # pasamos el fondo a la luz actual con una LUT por canal (brightness
    # transfer function, Javed 2005): para cada valor del fondo, la mediana
    # de esos pixeles en el frame actual. La mano no afecta mucho a la
    # mediana xq casi todo el recuadro sigue siendo fondo
    out = np.empty_like(background)
    for ch in range(3):
        bg = background[::step, ::step, ch].ravel()
        fr = frame[::step, ::step, ch].ravel().astype(np.int32)
        bins = (bg // bin_size).astype(np.int32)
        counts = np.bincount(bins, minlength=256 // bin_size)

        # mediana de cada bin sin bucle: ordeno por (bin, valor) y cojo el del medio
        ordered = np.sort(bins * 256 + fr)
        starts = np.cumsum(counts) - counts
        ok = np.where(counts >= min_pixels)[0]
        ys = ordered[starts[ok] + counts[ok] // 2] - ok * 256
        xs = np.bincount(bins, weights=bg, minlength=len(counts))[ok] / counts[ok]

        if len(xs) < 2:
            out[..., ch] = background[..., ch]
            continue
        lut = np.clip(np.interp(np.arange(256), xs, ys), 0, 255).astype(np.uint8)
        out[..., ch] = cv2.LUT(background[..., ch], lut)
    return out


def _fill_holes(mask):
    h, w = mask.shape
    flood = np.zeros((h + 2, w + 2), np.uint8)
    flood[1:-1, 1:-1] = mask
    cv2.floodFill(flood, np.zeros((h + 4, w + 4), np.uint8), (0, 0), 255)
    holes = cv2.bitwise_not(flood)[1:-1, 1:-1]
    return cv2.bitwise_or(mask, holes)


def segment_hand(frame, background, roi=None, debug=False):
    if frame.shape != background.shape:
        raise ValueError("frame and background must have the same size "
                         f"({frame.shape} vs {background.shape})")
    H, W = frame.shape[:2]
    if roi is None:
        roi = config.roi_pixels(W, H)
    x, y, w, h = roi
    fr = frame[y:y + h, x:x + w]
    bg = background[y:y + h, x:x + w]

    matched = match_brightness(bg, fr)

    fr_ycc = cv2.cvtColor(fr, cv2.COLOR_BGR2YCrCb)
    bg_ycc = cv2.cvtColor(matched, cv2.COLOR_BGR2YCrCb)
    d = cv2.absdiff(fr_ycc, bg_ycc).astype(np.float32)
    score = config.BG_WEIGHT_Y * d[..., 0] + d[..., 1] + d[..., 2]
    score = cv2.GaussianBlur(score, (5, 5), 0)
    changed = np.uint8(score > config.BG_THRESHOLD) * 255

    # cierre grande + rellenar huecos para que la palma salga entera
    # (a media resolucion, va 4 veces mas rapido y da lo mismo)
    small = cv2.resize(changed, (w // 2, h // 2), interpolation=cv2.INTER_NEAREST)
    small = cv2.morphologyEx(small, cv2.MORPH_CLOSE, _ellipse(config.FG_CLOSE_KERNEL // 2 | 1))
    small = _fill_holes(small)
    changed_filled = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)

    # AND con piel: quita manga, pulsera y la pared que se ve por dentro de la O
    skin = cv2.inRange(fr_ycc, config.SKIN_LOWER, config.SKIN_UPPER)
    hand = cv2.bitwise_and(changed_filled, skin)
    hand = cv2.morphologyEx(hand, cv2.MORPH_OPEN, _ellipse(config.OPEN_KERNEL))
    hand = cv2.morphologyEx(hand, cv2.MORPH_CLOSE, _ellipse(config.CLOSE_KERNEL))

    mask = np.zeros((H, W), np.uint8)
    mask[y:y + h, x:x + w] = hand
    if not debug:
        return mask

    # pasos intermedios para la figura del informe
    steps = {"frame": fr, "background": bg, "matched": matched,
             "score": np.clip(score * 4, 0, 255).astype(np.uint8),
             "changed": changed, "changed_filled": changed_filled,
             "skin": skin, "mask": hand}
    return mask, steps
