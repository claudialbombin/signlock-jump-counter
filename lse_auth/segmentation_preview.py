"""
Step 3 - Check the hand segmentation, offline or live.

Usage
-----
    python -m lse_auth.segmentation_preview                # live camera
    python -m lse_auth.segmentation_preview --dataset      # whole dataset
    python -m lse_auth.segmentation_preview --sequence O/img_40.jpg

In the live view, if the hand shows one of the letters the classifier
already knows (H, O or L for now, step 6), the letter is written on screen
together with the contour, the palm centre and the fingertips. A bar under
the letter fills while the step 7 detector confirms it, and the confirmed
letters (one per sign held, not one per frame) are listed at the bottom.
They go to the step 8 sequence decoder: the bottom line shows the progress
of the code (H-O-_-_) and DESBLOQUEADO once it is complete. While the A is
not recognised, `--code HOL` tries the whole flow with a shorter code.

Live controls
-------------
    f        (re)capture the background: take the hand out of the box first
    r        clear the confirmed letters and lock again
    s        save the transformation sequence of the current frame
    e        save the current frame + background in errores/ (when the
             letter is wrong), to reproduce it later with --errors
    q / ESC  quit

--dataset runs segment_hand on every image that has a background in
backgrounds.csv, prints the time, the hand area and the letters predicted
per class and saves a
contact sheet (image | mask) in pasos/lse/figuras/segmentacion_dataset.jpg.

--sequence saves the figure "secuencia de transformación de la imagen" that
the report asks for: frame -> background -> background with the frame's
exposure -> difference -> changed -> filled -> skin -> hand.
"""

import argparse
import glob
import os
import time
from collections import Counter
from typing import Dict, List, Optional

import cv2
import numpy as np

from lse_auth import config, dataset
from lse_auth.alphabet import CLASS_LABELS
from lse_auth.classifier import classify
from lse_auth.contours import find_hand_contour
from lse_auth.features import extract_features
from lse_auth.segmentation import BackgroundModel, segment_hand
from lse_auth.sequence_decoder import Event, SequenceDecoder
from lse_auth.stabilizer import State, StableLetterDetector

FIGURES_DIR = os.path.join(config.PROJECT_ROOT, "pasos", "lse", "figuras")
ERRORS_DIR = os.path.join(config.PROJECT_ROOT, "errores")     # not in git (faces, rooms)
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
    x, y, w, h = config.roi_pixels(frame.shape[1], frame.shape[0])
    # Only the ROI can contain hand pixels: blend there, with OpenCV (fast)
    roi, hand = view[y:y + h, x:x + w], mask[y:y + h, x:x + w]
    tinted = cv2.add(cv2.multiply(roi, (0.5, 0.5, 0.5, 0)), (0, 127, 0, 0))
    cv2.copyTo(tinted, hand, roi)
    cv2.rectangle(view, (x, y), (x + w, y + h), (0, 255, 0), 2)
    return view


def recognise(mask: np.ndarray):
    """
    Steps 4-6 on a hand mask.

    Returns
    -------
    (letter, hand, features)
        letter is "H", "O", "L" or None; hand and features are None when there
        is no hand in the ROI.
    """
    hand = find_hand_contour(mask)
    if hand is None:
        return None, None, None
    features = extract_features(hand)
    return classify(features), hand, features


def draw_recognition(view: np.ndarray, letter: Optional[str], hand, features) -> None:
    """Draw contour, palm, fingertips and the recognised letter (in place)."""
    if hand is None:
        return
    color = (0, 255, 0) if letter else (0, 200, 255)
    cv2.drawContours(view, [hand.contour], -1, color, 2, cv2.LINE_8)
    cv2.circle(view, hand.palm_center, int(hand.palm_radius), (255, 0, 0), 2)
    for tip in features.fingertips:
        cv2.line(view, hand.palm_center, tip, (255, 0, 0), 1, cv2.LINE_AA)
        cv2.circle(view, tip, 8, (0, 0, 255), -1)

    x, y, w, _ = config.roi_pixels(view.shape[1], view.shape[0])
    text = letter if letter else "?"
    cv2.putText(view, text, (x + w + 15, y + 110), cv2.FONT_HERSHEY_SIMPLEX,
                4.0, (0, 0, 0), 14, cv2.LINE_AA)
    cv2.putText(view, text, (x + w + 15, y + 110), cv2.FONT_HERSHEY_SIMPLEX,
                4.0, color, 6, cv2.LINE_AA)
    cv2.putText(view, f"{features.n_fingers} dedo{'' if features.n_fingers == 1 else 's'}", (x + w + 15, y + 150),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2, cv2.LINE_AA)
    # Widths in palm radii next to each tip: ~0.5 one finger, ~1 two together
    for finger in features.fingers:
        cv2.putText(view, f"{finger.width:.2f}", (finger.tip[0] + 10, finger.tip[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)

    # A hand cut by the box is not classified: ask to bring it inside
    if features.cut:
        cv2.putText(view, "Mete toda la mano en el recuadro", (x, y - 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2, cv2.LINE_AA)


class LetterSmoother:
    """
    Majority vote over the last frames, so a single bad frame does not
    change the letter on screen. It only makes the display calm: the
    letters that count are the ones confirmed by StableLetterDetector.

    A letter is shown only when it wins at least MIN_SHARE of the window.
    """

    def __init__(self, window: int = 9, min_share: float = 0.6) -> None:
        self.window, self.min_share = window, min_share
        self.history: List[Optional[str]] = []

    def update(self, letter: Optional[str]) -> Optional[str]:
        self.history = (self.history + [letter])[-self.window:]
        best, count = Counter(self.history).most_common(1)[0]
        return best if count >= self.min_share * self.window else None


class FrameGrabber:
    """
    Read the camera in a background thread and keep only the newest frame.

    Without it, the loop waits for the camera (reading + undistorting) and
    then for the processing, one after the other. With it both happen at
    the same time and the processing always gets the most recent frame.
    """

    def __init__(self, cam) -> None:
        import threading
        self.cam = cam
        self.frame: Optional[np.ndarray] = None
        self.count = 0                    # frames delivered by the camera
        self.running = True
        self._lock = threading.Lock()
        self._new = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        while self.running:
            frame = self.cam.read()
            if frame is None:
                self.running = False
                break
            with self._lock:
                self.frame = frame
                self.count += 1
            self._new.set()

    def read(self, timeout: float = 2.0) -> Optional[np.ndarray]:
        """Newest frame not returned yet (waits for it), or None if the camera stopped."""
        if not self._new.wait(timeout) or not self.running:
            return None
        with self._lock:
            self._new.clear()
            return self.frame

    def stop(self) -> None:
        self.running = False
        self._thread.join(timeout=1.0)


def draw_stabilizer(view: np.ndarray, detector: StableLetterDetector,
                    decoder: SequenceDecoder) -> None:
    """Progress of the letter being confirmed and of the code (in place)."""
    x, y, w, _ = config.roi_pixels(view.shape[1], view.shape[0])
    bar_x, bar_y, bar_w = x + w + 15, y + 170, 150
    if detector.state is State.CONFIRMING:
        cv2.rectangle(view, (bar_x, bar_y), (bar_x + bar_w, bar_y + 14), (255, 255, 255), 1)
        cv2.rectangle(view, (bar_x, bar_y),
                      (bar_x + int(bar_w * detector.progress), bar_y + 14), (0, 255, 0), -1)
    elif detector.state is State.WAITING_RESET:
        cv2.putText(view, f"{detector.confirmed} ok - cambia de letra", (bar_x, bar_y + 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2, cv2.LINE_AA)

    # Code progress (step 8) and the last event for 2 s
    now = time.monotonic()
    color = (0, 255, 0) if decoder.is_unlocked() else (255, 255, 255)
    text = decoder.progress_text + ("   DESBLOQUEADO" if decoder.is_unlocked() else "")
    left = decoder.time_left(now)
    if left is not None:
        text += f"   ({left:.0f} s)"
    last = decoder.last_event
    if last is not None and now - last[0] < 2.0:
        if last[1] is Event.WRONG:
            text, color = f"{decoder.progress_text}   Secuencia incorrecta", (0, 0, 255)
        elif last[1] is Event.TIMEOUT:
            text, color = f"{decoder.progress_text}   Tiempo agotado", (0, 0, 255)
        elif last[1] in (Event.CORRECT, Event.RESTART):
            color = (0, 255, 0)
    org = (20, view.shape[0] - 25)
    cv2.putText(view, text, org, cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 6, cv2.LINE_AA)
    cv2.putText(view, text, org, cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 2, cv2.LINE_AA)


def save_error(frame: np.ndarray, background: np.ndarray) -> None:
    """Keep a misclassified frame and its background to reproduce it offline."""
    os.makedirs(ERRORS_DIR, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    cv2.imwrite(os.path.join(ERRORS_DIR, f"{stamp}_frame.png"), frame)
    cv2.imwrite(os.path.join(ERRORS_DIR, f"{stamp}_background.png"), background)
    print(f"Saved errores/{stamp}_frame.png (+ background)")


def run_errors() -> None:
    """Recognise every frame saved with the e key and print its features."""
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
        fingers = ([(f.angle, f.width, f.length) for f in features.fingers]
                   if features else [])
        print(f"{os.path.basename(path)}: {letter or '-'}  hole={bool(hand and hand.has_hole)}"
              f"  fingers (angle, width, length)={fingers}")


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
        predicted: Counter = Counter()
        paired = [p for p in dataset.list_images(label)
                  if dataset.background_for(p) is not None]
        for i, path in enumerate(paired):
            image, background = cv2.imread(path), dataset.background_for(path)
            start = time.perf_counter()
            mask = segment_hand(image, background)
            times.append(time.perf_counter() - start)
            areas.append(int(np.count_nonzero(mask)))
            predicted[recognise(mask)[0] or "-"] += 1
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
              f"{min(areas)}-{max(areas)} px (median {int(np.median(areas))}), "
              f"predicted {dict(predicted)}")
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


def run_live(code: str = "".join(config.UNLOCK_SEQUENCE)) -> None:
    """Live view: background capture, mask overlay and FPS."""
    from lse_auth.camera import Camera     # only needed with a camera

    model = BackgroundModel()
    smoother = LetterSmoother()
    detector = StableLetterDetector()
    decoder = SequenceDecoder(code=code.upper())
    capturing = True                       # start by learning the background
    fps, proc_ms, last = 0.0, 0.0, time.perf_counter()
    cam_count, cam_fps, cam_t = 0, 0.0, time.perf_counter()
    with Camera() as cam:
        grabber = FrameGrabber(cam)
        cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL)
        while True:
            frame = grabber.read()
            if frame is None:
                break
            start = time.perf_counter()
            if capturing:
                capturing = not model.add(frame)
                view = frame.copy()
                cv2.putText(view, "Saving background: keep the box empty",
                            (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0,
                            (0, 0, 255), 2, cv2.LINE_AA)
            else:
                mask = segment_hand(frame, model.image)
                letter, hand, features = recognise(mask)
                view = overlay_mask(frame, mask)
                draw_recognition(view, smoother.update(letter), hand, features)
                new = detector.update(letter)
                if new is not None:
                    print(f"[stabilizer] confirmed {new}")
                    decoder.feed(new)
                decoder.tick()
                draw_stabilizer(view, detector, decoder)
            proc_ms = 0.9 * proc_ms + 0.1 * 1000 * (time.perf_counter() - start)

            # FPS shown = frames processed per second. The camera rate and
            # the processing time are shown too, to know which one limits.
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
            elif key == ord("s") and model.ready:
                _, steps = segment_hand(frame, model.image, debug=True)
                _save(sequence_figure(steps), f"secuencia_live_{int(time.time())}.png")
            elif key == ord("e") and model.ready:
                save_error(frame, model.image)
        grabber.stop()
    cv2.destroyAllWindows()


def main() -> None:
    parser = argparse.ArgumentParser(description="Check the step 3 hand segmentation.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--dataset", action="store_true",
                       help="segment every dataset image that has a background")
    group.add_argument("--sequence", metavar="CLASS/img_XX.jpg",
                       help="save the transformation sequence of one dataset image")
    group.add_argument("--errors", action="store_true",
                       help="recognise the frames saved with e in errores/")
    parser.add_argument("--code", default="".join(config.UNLOCK_SEQUENCE),
                        help="unlock code for the live view (e.g. HOL while A is not recognised)")
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
