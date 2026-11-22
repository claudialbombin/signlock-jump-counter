"""
Step 3 - Check the hand segmentation, offline or live.

Usage
-----
    python -m lse_auth.segmentation_preview                # live camera
    python -m lse_auth.segmentation_preview --dataset      # whole dataset
    python -m lse_auth.segmentation_preview --sequence O/img_40.jpg

Live controls
-------------
    f        (re)capture the background: take the hand out of the box first
    s        save the transformation sequence of the current frame
    q / ESC  quit

--dataset runs segment_hand on every image that has a background in
backgrounds.csv, prints the time and the hand area per class and saves a
contact sheet (image | mask) in pasos/lse/figuras/segmentacion_dataset.jpg.

--sequence saves the figure "secuencia de transformación de la imagen" that
the report asks for: frame -> background -> background with the frame's
exposure -> difference -> changed -> filled -> skin -> hand.
"""

import argparse
import os
import time
from typing import Dict, List

import cv2
import numpy as np

from lse_auth import config, dataset
from lse_auth.alphabet import CLASS_LABELS
from lse_auth.segmentation import BackgroundModel, segment_hand

FIGURES_DIR = os.path.join(config.PROJECT_ROOT, "pasos", "lse", "figuras")
WINDOW = "Hand segmentation - f: background, s: save, q: quit"

# Order and captions of the transformation sequence
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


def _to_bgr(image: np.ndarray) -> np.ndarray:
    """Grey masks to BGR so they can be stacked with colour images."""
    return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR) if image.ndim == 2 else image


def sequence_figure(steps: Dict[str, np.ndarray], tile_width: int = 280) -> np.ndarray:
    """
    Build the transformation sequence as a 2 x 4 grid with captions.

    Parameters
    ----------
    steps : dict
        Intermediate images returned by segment_hand(..., debug=True).
    tile_width : int
        Width of each tile in pixels.
    """
    tiles = []
    for key, caption in SEQUENCE:
        image = _to_bgr(steps[key])
        h, w = image.shape[:2]
        tile = cv2.resize(image, (tile_width, int(h * tile_width / w)),
                          interpolation=cv2.INTER_AREA)
        band = np.full((30, tile_width, 3), 255, np.uint8)
        cv2.putText(band, caption, (5, 21), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    (0, 0, 0), 1, cv2.LINE_AA)
        tiles.append(np.vstack([band, tile]))
    gap = np.full((tiles[0].shape[0], 6, 3), 255, np.uint8)
    rows = [np.hstack(sum(([t, gap] for t in tiles[i:i + 4]), [])[:-1])
            for i in (0, 4)]
    return np.vstack([rows[0], np.full((6, rows[0].shape[1], 3), 255, np.uint8), rows[1]])


def overlay_mask(frame: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Frame with the hand painted in green and the ROI drawn."""
    view = frame.copy()
    view[mask > 0] = (0.5 * view[mask > 0] + (0, 127, 0)).astype(np.uint8)
    x, y, w, h = config.roi_pixels(frame.shape[1], frame.shape[0])
    cv2.rectangle(view, (x, y), (x + w, y + h), (0, 255, 0), 2)
    return view


def _save(image: np.ndarray, name: str) -> str:
    os.makedirs(FIGURES_DIR, exist_ok=True)
    path = os.path.join(FIGURES_DIR, name)
    cv2.imwrite(path, image)
    print(f"Saved {os.path.relpath(path, config.PROJECT_ROOT)}")
    return path


def run_dataset(per_class: int = 6, thumb_width: int = 150) -> None:
    """Segment every image with a background and summarise the result."""
    times: List[float] = []
    rows = []
    for label in CLASS_LABELS:
        areas, tiles = [], []
        paired = [p for p in dataset.list_images(label)
                  if dataset.background_for(p) is not None]
        for i, path in enumerate(paired):
            image, background = cv2.imread(path), dataset.background_for(path)
            start = time.perf_counter()
            mask = segment_hand(image, background)
            times.append(time.perf_counter() - start)
            areas.append(int(np.count_nonzero(mask)))
            if i < per_class:
                x, y, w, h = config.roi_pixels(image.shape[1], image.shape[0])
                pair = np.hstack([image[y:y + h, x:x + w],
                                  _to_bgr(mask[y:y + h, x:x + w])])
                tiles.append(cv2.resize(pair, (2 * thumb_width,
                                               int(pair.shape[0] * 2 * thumb_width / pair.shape[1]))))
        if not paired:
            print(f"  {label:5s} no images with background")
            continue
        print(f"  {label:5s} {len(paired):3d} images, hand area "
              f"{min(areas)}-{max(areas)} px (median {int(np.median(areas))})")
        row = np.hstack(tiles)
        cv2.putText(row, label, (8, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0,
                    (0, 0, 255), 2, cv2.LINE_AA)
        rows.append(row)

    if not rows:
        print("No image has a background yet (see pasos/lse/dataset_lse/README.md).")
        return
    print(f"segment_hand: median {1000 * np.median(times):.1f} ms, "
          f"max {1000 * max(times):.1f} ms per frame")
    width = max(r.shape[1] for r in rows)
    rows = [np.hstack([r, np.full((r.shape[0], width - r.shape[1], 3), 255, np.uint8)])
            for r in rows]
    _save(np.vstack(rows), "segmentacion_dataset.jpg")


def run_sequence(relative_path: str) -> None:
    """Save the transformation sequence of one dataset image."""
    path = os.path.join(config.DATASET_DIR, relative_path)
    background = dataset.background_for(path)
    if background is None:
        raise SystemExit(f"{relative_path} has no background in backgrounds.csv")
    _, steps = segment_hand(cv2.imread(path), background, debug=True)
    name = "secuencia_" + relative_path.replace("/", "_").rsplit(".", 1)[0] + ".png"
    _save(sequence_figure(steps), name)


def run_live() -> None:
    """Live view: background capture, mask overlay and FPS."""
    from lse_auth.camera import Camera     # only needed with a camera

    model = BackgroundModel()
    capturing = True                       # start by learning the background
    fps, last = 0.0, time.perf_counter()
    with Camera() as cam:
        cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL)
        while True:
            frame = cam.read()
            if frame is None:
                break
            if capturing:
                capturing = not model.add(frame)
                view = frame.copy()
                cv2.putText(view, "Saving background: keep the box empty",
                            (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0,
                            (0, 0, 255), 2, cv2.LINE_AA)
                steps = None
            else:
                mask, steps = segment_hand(frame, model.image, debug=True)
                view = overlay_mask(frame, mask)

            now = time.perf_counter()
            fps = 0.9 * fps + 0.1 / max(now - last, 1e-6)
            last = now
            cv2.putText(view, f"{fps:5.1f} FPS", (view.shape[1] - 170, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2, cv2.LINE_AA)
            cv2.imshow(WINDOW, view)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                break
            if key == ord("f"):
                model.reset()
                capturing = True
            elif key == ord("s") and steps is not None:
                _save(sequence_figure(steps), f"secuencia_live_{int(time.time())}.png")
    cv2.destroyAllWindows()


def main() -> None:
    parser = argparse.ArgumentParser(description="Check the step 3 hand segmentation.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--dataset", action="store_true",
                       help="segment every dataset image that has a background")
    group.add_argument("--sequence", metavar="CLASS/img_XX.jpg",
                       help="save the transformation sequence of one dataset image")
    args = parser.parse_args()

    if args.dataset:
        run_dataset()
    elif args.sequence:
        run_sequence(args.sequence)
    else:
        run_live()


if __name__ == "__main__":
    main()
