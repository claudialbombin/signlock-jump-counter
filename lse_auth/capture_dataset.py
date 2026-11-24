# paso 2: capturar el dataset con la camara calibrada
#   python -m lse_auth.capture_dataset            capturar
#   python -m lse_auth.capture_dataset --summary  contar + hoja de miniaturas
#
# f = guardar el fondo VACIO (al empezar y si cambia la luz), 0-4 clase,
# c/espacio = foto, b = rafaga, d = deshacer, q = salir
# no deja hacer fotos sin fondo. No mover la camara durante la sesion

import argparse
import os

import cv2
import numpy as np

from lse_auth import config, dataset
from lse_auth.alphabet import CLASS_LABELS, LETTERS, key_to_label
from lse_auth.camera import Camera

TARGET_PER_CLASS = 20
BURST_SIZE = 5
BURST_GAP = 8          # ~0.25 s entre fotos de la rafaga
BG_FRAMES = 30
WINDOW = "Dataset capture - press q to quit"


def draw_overlay(frame, label, counts, message, burst_left, has_background):
    view = frame.copy()
    h, w = view.shape[:2]

    x, y, rw, rh = config.roi_pixels(w, h)
    cv2.rectangle(view, (x, y), (x + rw, y + rh), (0, 0, 255) if burst_left else (0, 255, 0), 2)

    cv2.rectangle(view, (0, 0), (w, 70), (0, 0, 0), -1)
    cv2.putText(view, f"Class: {label}", (15, 45), cv2.FONT_HERSHEY_SIMPLEX,
                1.3, (255, 255, 255), 3, cv2.LINE_AA)
    if not has_background:
        cv2.putText(view, "Empty the box and press f (background)", (x, y - 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2, cv2.LINE_AA)

    # contador de cada clase, en verde cuando ya hay suficientes
    xt = 320
    for i, name in enumerate(CLASS_LABELS):
        n = counts.get(name, 0)
        if name == label:
            color = (0, 255, 255)
        elif n >= TARGET_PER_CLASS:
            color = (0, 255, 0)
        else:
            color = (200, 200, 200)
        cv2.putText(view, f"{i}:{name} {n}", (xt, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                    color, 2, cv2.LINE_AA)
        xt += 150

    cv2.rectangle(view, (0, h - 75), (w, h), (0, 0, 0), -1)
    if label in LETTERS:
        hint = LETTERS[label].description
    else:
        hint = "No sign: relaxed hand, other gestures or empty background."
    cv2.putText(view, hint, (15, h - 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(view, message, (15, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                (0, 255, 255), 2, cv2.LINE_AA)
    return view


def run_capture():
    label = CLASS_LABELS[1]       # empezamos por la H
    counts = dataset.count_images()
    saved = []                    # para poder deshacer con d
    message = "First take the hand out of the box and press f"
    burst_left, n_frame = 0, 0
    bg_path = None
    bg_sum, bg_left = None, 0

    with Camera() as cam:
        print(f"Camera at {cam.frame_size[0]}x{cam.frame_size[1]}, "
              f"calibration RMS = {cam.undistorter.rms:.3f} px")
        cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL)

        while True:
            frame = cam.read()
            if frame is None:
                print("No frame received (the camera may have been disconnected).")
                break
            n_frame += 1

            if bg_left:
                bg_sum += frame.astype(np.float32)
                bg_left -= 1
                if not bg_left:
                    bg = (bg_sum / BG_FRAMES).round().astype(np.uint8)
                    bg_path = dataset.save_background(bg)
                    message = f"Background saved ({os.path.basename(bg_path)}), keep the camera still"

            if burst_left and n_frame % BURST_GAP == 0:
                path = dataset.save_image(frame, label)
                dataset.link_background(path, bg_path)
                saved.append(path)
                counts[label] += 1
                burst_left -= 1
                message = f"Burst: saved {os.path.basename(path)} ({burst_left} left)"

            cv2.imshow(WINDOW, draw_overlay(frame, label, counts, message, burst_left,
                                            bg_path is not None))
            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                break

            new_label = key_to_label(key)
            if new_label is not None:
                label = new_label
                message = f"Class changed to {label}"
            elif key == ord("f") and not bg_left and not burst_left:
                bg_sum = np.zeros(frame.shape, np.float32)
                bg_left = BG_FRAMES
                message = "Saving background, keep the box empty..."
            elif key in (ord("c"), ord(" "), ord("b")) and bg_path is None:
                message = "No background yet: empty the box and press f first"
            elif key in (ord("c"), ord(" ")) and not bg_left:
                path = dataset.save_image(frame, label)
                dataset.link_background(path, bg_path)
                saved.append(path)
                counts[label] += 1
                message = f"Saved {os.path.relpath(path, config.PROJECT_ROOT)}"
            elif key == ord("b") and not burst_left and not bg_left:
                burst_left = BURST_SIZE
                message = "Burst started, move the hand slightly"
            elif key == ord("d"):
                if saved:
                    path = saved.pop()
                    os.remove(path)
                    dataset.unlink_background(path)
                    counts[os.path.basename(os.path.dirname(path))] -= 1
                    message = f"Deleted {os.path.relpath(path, config.PROJECT_ROOT)}"
                else:
                    message = "Nothing to delete in this session"

    cv2.destroyAllWindows()
    print(f"{len(saved)} images saved in this session.")
    print_summary()


def print_summary(save_sheet=False):
    print("Images per class:")
    for label, n in dataset.count_images().items():
        status = "OK" if n >= TARGET_PER_CLASS else f"{TARGET_PER_CLASS - n} missing"
        print(f"  {label:5s} {n:3d}  ({status})")
    if save_sheet:
        os.makedirs(config.DATASET_DIR, exist_ok=True)   # si no existe imwrite falla sin avisar
        path = os.path.join(config.DATASET_DIR, "overview.jpg")
        cv2.imwrite(path, dataset.contact_sheet())
        print(f"Contact sheet saved to {path}")


def main():
    parser = argparse.ArgumentParser(description="Capture the LSE reference dataset.")
    parser.add_argument("--summary", action="store_true",
                        help="do not open the camera, only print counts and "
                             "save a contact sheet of the dataset")
    args = parser.parse_args()
    if args.summary:
        print_summary(save_sheet=True)
    else:
        run_capture()


if __name__ == "__main__":
    main()
