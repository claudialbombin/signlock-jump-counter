"""
Step 2 - Capture the reference dataset of LSE hand shapes.

Opens the calibrated camera, shows the live (undistorted, mirrored) image with
the hand ROI drawn on top, and saves labelled frames into
pasos/lse/dataset_lse/<class>/img_XX.jpg.

Controls
--------
    0 .. 4        choose the class: 0 = NONE, 1 = H, 2 = O, 3 = L, 4 = A
    c / SPACE     capture one image of the current class
    b             burst: capture BURST_SIZE images, one every BURST_GAP frames
                  (move the hand a little while it runs to get variety)
    d             delete the last image captured in this session (undo)
    q / ESC       quit

The overlays (text, ROI box) are drawn on a COPY of the frame, so the saved
images are clean.

Usage
-----
    python -m lse_auth.capture_dataset              # live capture
    python -m lse_auth.capture_dataset --summary    # counts + contact sheet
"""

import argparse
import os
from typing import List

import cv2
import numpy as np

from lse_auth import config, dataset
from lse_auth.alphabet import CLASS_LABELS, LETTERS, key_to_label
from lse_auth.camera import Camera

TARGET_PER_CLASS = 20    # the plan asks for ~15-20 images per class
BURST_SIZE = 5
BURST_GAP = 8            # frames between two burst captures (~0.25 s at 30 fps)
WINDOW = "Dataset capture - press q to quit"


def draw_overlay(frame: np.ndarray, label: str, counts: dict,
                 message: str, burst_left: int) -> np.ndarray:
    """
    Draw the user interface on a copy of the frame.

    Parameters
    ----------
    frame : np.ndarray
        Clean frame from the camera (it is not modified).
    label : str
        Class currently selected.
    counts : dict
        Number of images already saved per class.
    message : str
        Last status message (e.g. the path of the last saved image).
    burst_left : int
        Images left in the current burst (0 if no burst is running).

    Returns
    -------
    np.ndarray
        Frame with the overlay.
    """
    view = frame.copy()
    h, w = view.shape[:2]

    # Hand ROI: the user should keep the hand inside this box
    x, y, rw, rh = config.roi_pixels(w, h)
    roi_color = (0, 0, 255) if burst_left else (0, 255, 0)
    cv2.rectangle(view, (x, y), (x + rw, y + rh), roi_color, 2)

    # Dark band on top so the text is readable over any background
    cv2.rectangle(view, (0, 0), (w, 70), (0, 0, 0), -1)
    cv2.putText(view, f"Class: {label}", (15, 45), cv2.FONT_HERSHEY_SIMPLEX,
                1.3, (255, 255, 255), 3, cv2.LINE_AA)

    # Counter of every class, green when the target is reached
    x_text = 320
    for i, name in enumerate(CLASS_LABELS):
        n = counts.get(name, 0)
        color = (0, 255, 0) if n >= TARGET_PER_CLASS else (200, 200, 200)
        if name == label:
            color = (0, 255, 255)
        cv2.putText(view, f"{i}:{name} {n}", (x_text, 45),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2, cv2.LINE_AA)
        x_text += 150

    # Dark band at the bottom too, for the hint and the status message
    cv2.rectangle(view, (0, h - 75), (w, h), (0, 0, 0), -1)

    # Reminder of the expected hand shape (from step 1)
    hint = LETTERS[label].description if label in LETTERS else \
        "No sign: relaxed hand, other gestures or empty background."
    cv2.putText(view, hint, (15, h - 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(view, message, (15, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                (0, 255, 255), 2, cv2.LINE_AA)
    return view


def run_capture() -> None:
    """Main loop of the interactive capture tool."""
    label = CLASS_LABELS[1]            # start with H
    counts = dataset.count_images()
    saved_this_session: List[str] = []
    message = "Choose a class (0-4) and press c to capture"
    burst_left, frame_counter = 0, 0

    with Camera() as cam:
        print(f"Camera at {cam.frame_size[0]}x{cam.frame_size[1]}, "
              f"calibration RMS = {cam.undistorter.rms:.3f} px")
        cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL)

        while True:
            frame = cam.read()
            if frame is None:
                print("No frame received (the camera may have been disconnected).")
                break
            frame_counter += 1

            # Burst mode: save one frame every BURST_GAP frames
            if burst_left and frame_counter % BURST_GAP == 0:
                path = dataset.save_image(frame, label)
                saved_this_session.append(path)
                counts[label] += 1
                burst_left -= 1
                message = f"Burst: saved {os.path.basename(path)} ({burst_left} left)"

            cv2.imshow(WINDOW, draw_overlay(frame, label, counts, message, burst_left))
            key = cv2.waitKey(1) & 0xFF

            if key in (ord("q"), 27):
                break
            new_label = key_to_label(key)
            if new_label is not None:
                label = new_label
                message = f"Class changed to {label}"
            elif key in (ord("c"), ord(" ")):
                path = dataset.save_image(frame, label)
                saved_this_session.append(path)
                counts[label] += 1
                message = f"Saved {os.path.relpath(path, config.PROJECT_ROOT)}"
            elif key == ord("b") and not burst_left:
                burst_left = BURST_SIZE
                message = "Burst started, move the hand slightly"
            elif key == ord("d"):
                if saved_this_session:
                    path = saved_this_session.pop()
                    os.remove(path)
                    removed_label = os.path.basename(os.path.dirname(path))
                    counts[removed_label] -= 1
                    message = f"Deleted {os.path.relpath(path, config.PROJECT_ROOT)}"
                else:
                    message = "Nothing to delete in this session"

    cv2.destroyAllWindows()
    print(f"{len(saved_this_session)} images saved in this session.")
    print_summary()


def print_summary(save_sheet: bool = False) -> None:
    """Print how many images each class has and optionally save a contact sheet."""
    counts = dataset.count_images()
    print("Images per class:")
    for label, n in counts.items():
        status = "OK" if n >= TARGET_PER_CLASS else f"{TARGET_PER_CLASS - n} missing"
        print(f"  {label:5s} {n:3d}  ({status})")

    if save_sheet:
        sheet = dataset.contact_sheet()
        os.makedirs(config.DATASET_DIR, exist_ok=True)   # imwrite fails silently otherwise
        path = os.path.join(config.DATASET_DIR, "overview.jpg")
        cv2.imwrite(path, sheet)
        print(f"Contact sheet saved to {path}")


def main() -> None:
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
