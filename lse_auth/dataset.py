"""
Helpers to read and write the reference dataset of step 2.

Folder layout (one sub-folder per class):

    pasos/lse/dataset_lse/
        NONE/img_01.jpg, img_02.jpg ...
        H/...
        O/...
        L/...
        A/...

The images are already undistorted when they are saved, so any later step
can load them and work as if they came straight from the live camera.

Background frames (added for step 3): the skin colour alone cannot separate
the hand from a wooden shelf or a warm-lit wall, so step 3 also subtracts a
picture of the empty scene. Every capture session starts by saving that
empty scene in _background/bg_XX.jpg, and backgrounds.csv remembers which
background belongs to each image:

    pasos/lse/dataset_lse/
        _background/bg_01.jpg ...
        backgrounds.csv            image,background (paths relative to the dataset)

Images captured before this existed simply have no background.

I save them as JPEG with high quality instead of PNG: a 1280x720 PNG of a
camera frame is ~1-2 MB, so ~100 images would make the repo very heavy,
while JPEG at quality 95 is ~10 times smaller and the difference is not
visible for skin segmentation.
"""

import csv
import glob
import os
import re
from typing import Dict, Iterator, List, Optional, Tuple

import cv2
import numpy as np

from lse_auth import config
from lse_auth.alphabet import CLASS_LABELS

IMAGE_EXT = ".jpg"
JPEG_QUALITY = 95
_NAME_PATTERN = re.compile(r"img_(\d+)\.(jpg|png)$")
_BG_PATTERN = re.compile(r"bg_(\d+)\.(jpg|png)$")
BACKGROUND_FOLDER = "_background"
PAIRS_FILE = "backgrounds.csv"


def class_dir(label: str, root: str = config.DATASET_DIR) -> str:
    """Return (and create if needed) the folder of one class."""
    if label not in CLASS_LABELS:
        raise ValueError(f"Unknown class '{label}', expected one of {CLASS_LABELS}")
    path = os.path.join(root, label)
    os.makedirs(path, exist_ok=True)
    return path


def list_images(label: str, root: str = config.DATASET_DIR) -> List[str]:
    """Sorted list of image paths of one class (empty if there are none)."""
    folder = os.path.join(root, label)
    paths = [p for p in glob.glob(os.path.join(folder, "img_*"))
             if _NAME_PATTERN.search(os.path.basename(p))]
    return sorted(paths)


def next_image_path(label: str, root: str = config.DATASET_DIR) -> str:
    """
    Path for the next image of a class, continuing the numbering.

    I look at the highest existing number instead of counting files, so if
    I delete a bad picture in the middle the next one does not overwrite
    an existing file.
    """
    numbers = [int(_NAME_PATTERN.search(os.path.basename(p)).group(1))
               for p in list_images(label, root)]
    index = max(numbers, default=0) + 1
    return os.path.join(class_dir(label, root), f"img_{index:02d}{IMAGE_EXT}")


def save_image(image: np.ndarray, label: str, root: str = config.DATASET_DIR) -> str:
    """
    Save a frame in the folder of its class.

    Returns
    -------
    str
        Path where the image was written.
    """
    path = next_image_path(label, root)
    if not cv2.imwrite(path, image, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY]):
        raise IOError(f"Could not write {path}")
    return path


def count_images(root: str = config.DATASET_DIR) -> Dict[str, int]:
    """Number of images per class."""
    return {label: len(list_images(label, root)) for label in CLASS_LABELS}


def iter_dataset(root: str = config.DATASET_DIR) -> Iterator[Tuple[str, str, np.ndarray]]:
    """
    Go through the whole dataset.

    Yields
    ------
    (label, path, image)
        Class label, file path and the BGR image.
    """
    for label in CLASS_LABELS:
        for path in list_images(label, root):
            image = cv2.imread(path)
            if image is not None:
                yield label, path, image


def contact_sheet(root: str = config.DATASET_DIR, per_class: int = 8,
                  thumb_width: int = 160) -> np.ndarray:
    """
    Build an overview image: one row per class with a few thumbnails.

    Useful to check at a glance that no picture ended up in the wrong
    folder, and to put in the report.
    """
    thumb_height = thumb_width * 9 // 16
    label_width = 90
    rows = []
    for label in CLASS_LABELS:
        row = np.full((thumb_height, label_width + per_class * thumb_width, 3),
                      255, dtype=np.uint8)
        cv2.putText(row, label, (8, thumb_height // 2 + 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 2, cv2.LINE_AA)
        for i, path in enumerate(list_images(label, root)[:per_class]):
            image = cv2.imread(path)
            if image is None:
                continue
            thumb = cv2.resize(image, (thumb_width, thumb_height),
                               interpolation=cv2.INTER_AREA)
            x0 = label_width + i * thumb_width
            row[:, x0:x0 + thumb_width] = thumb
        rows.append(row)
    return np.vstack(rows)


# ---------------------------------------------------------------------------
# Background frames (empty scene) for step 3
# ---------------------------------------------------------------------------

def save_background(image: np.ndarray, root: str = config.DATASET_DIR) -> str:
    """
    Save a picture of the empty scene as _background/bg_XX.jpg.

    Returns
    -------
    str
        Path where the background was written.
    """
    folder = os.path.join(root, BACKGROUND_FOLDER)
    os.makedirs(folder, exist_ok=True)
    numbers = [int(m.group(1)) for m in
               (_BG_PATTERN.search(os.path.basename(p))
                for p in glob.glob(os.path.join(folder, "bg_*"))) if m]
    path = os.path.join(folder, f"bg_{max(numbers, default=0) + 1:02d}{IMAGE_EXT}")
    if not cv2.imwrite(path, image, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY]):
        raise IOError(f"Could not write {path}")
    return path


def _read_pairs(root: str) -> Dict[str, str]:
    """Load backgrounds.csv as {image: background} (relative paths)."""
    path = os.path.join(root, PAIRS_FILE)
    if not os.path.exists(path):
        return {}
    with open(path, newline="") as f:
        return {row["image"]: row["background"] for row in csv.DictReader(f)}


def _write_pairs(pairs: Dict[str, str], root: str) -> None:
    """Rewrite backgrounds.csv, sorted so the diffs stay readable."""
    with open(os.path.join(root, PAIRS_FILE), "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["image", "background"])
        for image in sorted(pairs):
            writer.writerow([image, pairs[image]])


def _relative(path: str, root: str) -> str:
    """Path relative to the dataset root, always with forward slashes."""
    return os.path.relpath(path, root).replace(os.sep, "/")


def link_background(image_path: str, background_path: str,
                    root: str = config.DATASET_DIR) -> None:
    """Remember that image_path was captured in front of background_path."""
    pairs = _read_pairs(root)
    pairs[_relative(image_path, root)] = _relative(background_path, root)
    _write_pairs(pairs, root)


def unlink_background(image_path: str, root: str = config.DATASET_DIR) -> None:
    """Forget the background of an image (used when the image is deleted)."""
    pairs = _read_pairs(root)
    if pairs.pop(_relative(image_path, root), None) is not None:
        _write_pairs(pairs, root)


def background_for(image_path: str, root: str = config.DATASET_DIR) -> Optional[np.ndarray]:
    """
    Background image of a dataset picture, or None if it has none.

    Old images (captured before backgrounds were saved) return None, so the
    callers can skip them or fall back to colour-only segmentation.
    """
    background = _read_pairs(root).get(_relative(image_path, root))
    if background is None:
        return None
    return cv2.imread(os.path.join(root, background))
