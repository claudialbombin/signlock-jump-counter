"""
Helpers to read and write the reference dataset of step 2.

Folder layout (one sub-folder per class):

    pasos/dataset_lse/
        NONE/img_01.jpg, img_02.jpg ...
        H/...
        O/...
        L/...
        A/...

The images are already undistorted when they are saved, so any later step
can load them and work as if they came straight from the live camera.

I save them as JPEG with high quality instead of PNG: a 1280x720 PNG of a
camera frame is ~1-2 MB, so ~100 images would make the repo very heavy,
while JPEG at quality 95 is ~10 times smaller and the difference is not
visible for skin segmentation.
"""

import glob
import os
import re
from typing import Dict, Iterator, List, Tuple

import cv2
import numpy as np

from lse_auth import config
from lse_auth.alphabet import CLASS_LABELS

IMAGE_EXT = ".jpg"
JPEG_QUALITY = 95
_NAME_PATTERN = re.compile(r"img_(\d+)\.(jpg|png)$")


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
