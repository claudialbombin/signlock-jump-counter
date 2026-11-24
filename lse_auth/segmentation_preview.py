# para comprobar la segmentacion y las letras, en directo o con el dataset
#   python -m lse_auth.segmentation_preview                  directo
#   python -m lse_auth.segmentation_preview --dataset
#   python -m lse_auth.segmentation_preview --sequence O/img_40.jpg   figura del informe
#   python -m lse_auth.segmentation_preview --errors         los frames guardados con e
# teclas: f fondo, r bloquear, d capa debug, s guardar secuencia,
#         e guardar frame + fondo en errores/, q salir

import argparse
import glob
import os
import time
from collections import Counter

import cv2
import numpy as np

from lse_auth import config, dataset
from lse_auth.alphabet import CLASS_LABELS
from lse_auth.camera import FrameGrabber
from lse_auth.classifier import classify
from lse_auth.contours import find_hand_contour
from lse_auth.features import extract_features
from lse_auth.overlay import draw_overlay
from lse_auth.segmentation import BackgroundModel, segment_hand
from lse_auth.sequence_decoder import SequenceDecoder
from lse_auth.stabilizer import StableLetterDetector

FIGURES_DIR = os.path.join(config.PROJECT_ROOT, "pasos", "lse", "figuras")
ERRORS_DIR = os.path.join(config.PROJECT_ROOT, "errores")   # no se sube (salen caras)
WINDOW = "Hand segmentation - f: background, s: save, q: quit"

SEQUENCE = [
    ("frame", "1. Frame (ROI)"),
    ("background", "2. Fondo vacio"),
    ("matched", "3. Fondo con la exposicion actual"),
    ("score", "4. Diferencia YCrCb"),
    ("changed", "5. Pixeles que cambian"),
    ("changed_filled", "6. Cierre + relleno"),
    ("skin", "7. Rango de piel"),
    ("mask", "8. Mano = 6 AND 7"),
]


def _to_bgr(img):
    return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR) if img.ndim == 2 else img


def sequence_figure(steps, tile_width=280):
    # 2 filas de 4 con su titulo
    tiles = []
    for key, caption in SEQUENCE:
        img = _to_bgr(steps[key])
        h, w = img.shape[:2]
        tile = cv2.resize(img, (tile_width, int(h * tile_width / w)), interpolation=cv2.INTER_AREA)
        band = np.full((30, tile_width, 3), 255, np.uint8)
        cv2.putText(band, caption, (5, 21), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
        tiles.append(np.vstack([band, tile]))
    gap = np.full((tiles[0].shape[0], 6, 3), 255, np.uint8)
    rows = []
    for i in (0, 4):
        row = []
        for t in tiles[i:i + 4]:
            row += [t, gap]
        rows.append(np.hstack(row[:-1]))
    return np.vstack([rows[0], np.full((6, rows[0].shape[1], 3), 255, np.uint8), rows[1]])


def overlay_mask(frame, mask):
    view = frame.copy()
    x, y, w, h = config.roi_pixels(frame.shape[1], frame.shape[0])
    # solo puede haber mano dentro del recuadro, pinto solo ahi
    roi, hand = view[y:y + h, x:x + w], mask[y:y + h, x:x + w]
    tinted = cv2.add(cv2.multiply(roi, (0.5, 0.5, 0.5, 0)), (0, 127, 0, 0))
    cv2.copyTo(tinted, hand, roi)
    cv2.rectangle(view, (x, y), (x + w, y + h), (0, 255, 0), 2)
    return view


def recognise(mask):
    # pasos 4-6. Todo None si no hay mano
    hand = find_hand_contour(mask)
    if hand is None:
        return None, None, None
    features = extract_features(hand)
    return classify(features), hand, features


def draw_recognition(view, letter, hand, features, show_letter=True):
    # palma, puntas, anchos y n de dedos. Con show_letter tambien el contorno
    # y la letra (en directo eso ya lo pinta el overlay)
    if hand is None:
        return
    color = (0, 255, 0) if letter else (0, 200, 255)
    cv2.circle(view, hand.palm_center, int(hand.palm_radius), (255, 0, 0), 2)
    for tip in features.fingertips:
        cv2.line(view, hand.palm_center, tip, (255, 0, 0), 1, cv2.LINE_AA)
        cv2.circle(view, tip, 8, (0, 0, 255), -1)

    x, y, w, _ = config.roi_pixels(view.shape[1], view.shape[0])
    n = features.n_fingers
    cv2.putText(view, f"{n} dedo{'' if n == 1 else 's'}", (x + w + 15, y + 135),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2, cv2.LINE_AA)
    # ~0.5 un dedo, ~1 dos juntos
    for f in features.fingers:
        cv2.putText(view, f"{f.width:.2f}", (f.tip[0] + 10, f.tip[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)

    if not show_letter:
        return
    cv2.drawContours(view, [hand.contour], -1, color, 2, cv2.LINE_8)
    text = letter if letter else "?"
    cv2.putText(view, text, (x + w + 15, y + 110), cv2.FONT_HERSHEY_SIMPLEX, 4.0, (0, 0, 0), 14, cv2.LINE_AA)
    cv2.putText(view, text, (x + w + 15, y + 110), cv2.FONT_HERSHEY_SIMPLEX, 4.0, color, 6, cv2.LINE_AA)
    if features.cut:
        cv2.putText(view, "Mete toda la mano en el recuadro", (x, y - 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2, cv2.LINE_AA)


class LetterSmoother:
    # votacion de los ultimos frames, solo para que la letra de la pantalla
    # no salte. Las que cuentan son las del estabilizador

    def __init__(self, window=9, min_share=0.6):
        self.window, self.min_share = window, min_share
        self.history = []

    def update(self, letter):
        self.history = (self.history + [letter])[-self.window:]
        best, n = Counter(self.history).most_common(1)[0]
        return best if n >= self.min_share * self.window else None


def save_error(frame, background):
    os.makedirs(ERRORS_DIR, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    cv2.imwrite(os.path.join(ERRORS_DIR, f"{stamp}_frame.png"), frame)
    cv2.imwrite(os.path.join(ERRORS_DIR, f"{stamp}_background.png"), background)
    print(f"Saved errores/{stamp}_frame.png (+ background)")


def run_errors():
    frames = sorted(glob.glob(os.path.join(ERRORS_DIR, "*_frame.png")))
    if not frames:
        print("No frames in errores/ (press e in the live view to save one).")
        return
    for path in frames:
        background = cv2.imread(path.replace("_frame.png", "_background.png"))
        frame = cv2.imread(path)
        if background is None or frame is None:
            continue
        mask = segment_hand(frame, background)
        letter, hand, features = recognise(mask)
        view = overlay_mask(frame, mask)
        draw_recognition(view, letter, hand, features)
        cv2.imwrite(path.replace("_frame.png", "_result.jpg"), view)
        fingers = [(f.angle, f.width, f.length) for f in features.fingers] if features else []
        print(f"{os.path.basename(path)}: {letter or '-'}  hole={bool(hand and hand.has_hole)}"
              f"  fingers (angle, width, length)={fingers}")


def _save(image, name):
    os.makedirs(FIGURES_DIR, exist_ok=True)
    path = os.path.join(FIGURES_DIR, name)
    cv2.imwrite(path, image)
    print(f"Saved {os.path.relpath(path, config.PROJECT_ROOT)}")
    return path


def run_dataset(per_class=6, thumb_width=150):
    times = []
    rows = []
    for label in CLASS_LABELS:
        areas, tiles = [], []
        predicted = Counter()
        paired = [p for p in dataset.list_images(label) if dataset.background_for(p) is not None]
        for i, path in enumerate(paired):
            img, bg = cv2.imread(path), dataset.background_for(path)
            t0 = time.perf_counter()
            mask = segment_hand(img, bg)
            times.append(time.perf_counter() - t0)
            areas.append(int(np.count_nonzero(mask)))
            predicted[recognise(mask)[0] or "-"] += 1
            if i < per_class:
                x, y, w, h = config.roi_pixels(img.shape[1], img.shape[0])
                pair = np.hstack([img[y:y + h, x:x + w], _to_bgr(mask[y:y + h, x:x + w])])
                new_h = int(pair.shape[0] * 2 * thumb_width / pair.shape[1])
                tiles.append(cv2.resize(pair, (2 * thumb_width, new_h)))
        if not paired:
            print(f"  {label:5s} no images with background")
            continue
        print(f"  {label:5s} {len(paired):3d} images, hand area "
              f"{min(areas)}-{max(areas)} px (median {int(np.median(areas))}), "
              f"predicted {dict(predicted)}")
        row = np.hstack(tiles)
        cv2.putText(row, label, (8, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2, cv2.LINE_AA)
        rows.append(row)

    if not rows:
        print("No image has a background yet (see pasos/lse/dataset_lse/README.md).")
        return
    print(f"segment_hand: median {1000 * np.median(times):.1f} ms, "
          f"max {1000 * max(times):.1f} ms per frame")
    width = max(r.shape[1] for r in rows)
    rows = [np.hstack([r, np.full((r.shape[0], width - r.shape[1], 3), 255, np.uint8)]) for r in rows]
    _save(np.vstack(rows), "segmentacion_dataset.jpg")


def run_sequence(relative_path):
    path = os.path.join(config.DATASET_DIR, relative_path)
    bg = dataset.background_for(path)
    if bg is None:
        raise SystemExit(f"{relative_path} has no background in backgrounds.csv")
    _, steps = segment_hand(cv2.imread(path), bg, debug=True)
    name = "secuencia_" + relative_path.replace("/", "_").rsplit(".", 1)[0] + ".png"
    _save(sequence_figure(steps), name)


def run_live(code="".join(config.UNLOCK_SEQUENCE)):
    from lse_auth.camera import Camera

    model = BackgroundModel()
    smoother = LetterSmoother()
    detector = StableLetterDetector()
    decoder = SequenceDecoder(code=code.upper())
    capturing = True
    debug = True
    fps, proc_ms, last = 0.0, 0.0, time.perf_counter()
    cam_count, cam_fps, cam_t = 0, 0.0, time.perf_counter()
    with Camera() as cam:
        grabber = FrameGrabber(cam)
        cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL)
        while True:
            frame = grabber.read()
            if frame is None:
                break
            t0 = time.perf_counter()
            if capturing:
                capturing = not model.add(frame)
                view = frame.copy()
                cv2.putText(view, "Saving background: keep the box empty", (20, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2, cv2.LINE_AA)
            else:
                mask = segment_hand(frame, model.image)
                letter, hand, features = recognise(mask)
                shown = smoother.update(letter)
                new = detector.update(letter)
                if new is not None:
                    print(f"[stabilizer] confirmed {new}")
                    decoder.feed(new)
                decoder.tick()
                view = overlay_mask(frame, mask) if debug else frame.copy()
                if debug:
                    draw_recognition(view, shown, hand, features, show_letter=False)
                draw_overlay(view, hand, shown, detector, decoder, cut=bool(features and features.cut))
            proc_ms = 0.9 * proc_ms + 0.1 * 1000 * (time.perf_counter() - t0)

            # fps procesados, fps de la camara y ms de proceso, para ver cual limita
            now = time.perf_counter()
            fps = 0.9 * fps + 0.1 / max(now - last, 1e-6)
            last = now
            if now - cam_t >= 1.0:
                cam_fps = (grabber.count - cam_count) / (now - cam_t)
                cam_count, cam_t = grabber.count, now
            cv2.putText(view, f"{fps:5.1f} FPS", (view.shape[1] - 170, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(view, f"camara {cam_fps:4.1f} fps | proceso {proc_ms:4.1f} ms",
                        (view.shape[1] - 330, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                        (0, 255, 255), 1, cv2.LINE_AA)
            cv2.imshow(WINDOW, view)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                break
            if key == ord("f"):
                model.reset()
                detector.reset()
                capturing = True
            elif key == ord("r"):
                detector.reset()
                decoder.reset()
            elif key == ord("d"):
                debug = not debug
            elif key == ord("s") and model.ready:
                _, steps = segment_hand(frame, model.image, debug=True)
                _save(sequence_figure(steps), f"secuencia_live_{int(time.time())}.png")
            elif key == ord("e") and model.ready:
                save_error(frame, model.image)
        grabber.stop()
    cv2.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser(description="Check the step 3 hand segmentation.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--dataset", action="store_true",
                       help="segment every dataset image that has a background")
    group.add_argument("--sequence", metavar="CLASS/img_XX.jpg",
                       help="save the transformation sequence of one dataset image")
    group.add_argument("--errors", action="store_true",
                       help="recognise the frames saved with e in errores/")
    parser.add_argument("--code", default="".join(config.UNLOCK_SEQUENCE),
                        help="unlock code for the live view (default HOLA)")
    args = parser.parse_args()

    if args.dataset:
        run_dataset()
    elif args.sequence:
        run_sequence(args.sequence)
    elif args.errors:
        run_errors()
    else:
        run_live(args.code)


if __name__ == "__main__":
    main()
