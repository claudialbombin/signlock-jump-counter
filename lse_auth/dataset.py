# leer y guardar el dataset del paso 2
# dataset_lse/<clase>/img_XX.jpg, dataset_lse/_background/bg_XX.jpg
# y backgrounds.csv dice que fondo va con cada foto (las primeras no tienen)
# jpg 95 y no png xq los png de 1280x720 pesaban 1-2 MB

import csv
import glob
import os
import re

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


def class_dir(label, root=config.DATASET_DIR):
    if label not in CLASS_LABELS:
        raise ValueError(f"Unknown class '{label}', expected one of {CLASS_LABELS}")
    path = os.path.join(root, label)
    os.makedirs(path, exist_ok=True)
    return path


def list_images(label, root=config.DATASET_DIR):
    res = []
    for p in glob.glob(os.path.join(root, label, "img_*")):
        if _NAME_PATTERN.search(os.path.basename(p)):
            res.append(p)
    return sorted(res)


def next_image_path(label, root=config.DATASET_DIR):
    # el numero mas alto + 1 (si borro una del medio no se pisa ninguna)
    last = 0
    for p in list_images(label, root):
        last = max(last, int(_NAME_PATTERN.search(os.path.basename(p)).group(1)))
    return os.path.join(class_dir(label, root), f"img_{last + 1:02d}{IMAGE_EXT}")


def save_image(image, label, root=config.DATASET_DIR):
    path = next_image_path(label, root)
    if not cv2.imwrite(path, image, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY]):
        raise IOError(f"Could not write {path}")
    return path


def count_images(root=config.DATASET_DIR):
    return {label: len(list_images(label, root)) for label in CLASS_LABELS}


def iter_dataset(root=config.DATASET_DIR):
    for label in CLASS_LABELS:
        for path in list_images(label, root):
            img = cv2.imread(path)
            if img is not None:
                yield label, path, img


def contact_sheet(root=config.DATASET_DIR, per_class=8, thumb_width=160):
    # una fila por clase, para ver rapido que no hay fotos en la carpeta mala
    th = thumb_width * 9 // 16
    rows = []
    for label in CLASS_LABELS:
        row = np.full((th, 90 + per_class * thumb_width, 3), 255, dtype=np.uint8)
        cv2.putText(row, label, (8, th // 2 + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 2, cv2.LINE_AA)
        for i, path in enumerate(list_images(label, root)[:per_class]):
            img = cv2.imread(path)
            if img is None:
                continue
            x0 = 90 + i * thumb_width
            row[:, x0:x0 + thumb_width] = cv2.resize(img, (thumb_width, th), interpolation=cv2.INTER_AREA)
        rows.append(row)
    return np.vstack(rows)


def save_background(image, root=config.DATASET_DIR):
    folder = os.path.join(root, BACKGROUND_FOLDER)
    os.makedirs(folder, exist_ok=True)
    last = 0
    for p in glob.glob(os.path.join(folder, "bg_*")):
        m = _BG_PATTERN.search(os.path.basename(p))
        if m:
            last = max(last, int(m.group(1)))
    path = os.path.join(folder, f"bg_{last + 1:02d}{IMAGE_EXT}")
    if not cv2.imwrite(path, image, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY]):
        raise IOError(f"Could not write {path}")
    return path


def _read_pairs(root):
    path = os.path.join(root, PAIRS_FILE)
    if not os.path.exists(path):
        return {}
    pairs = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            pairs[row["image"]] = row["background"]
    return pairs


def _write_pairs(pairs, root):
    # ordenado para que los diffs de git se lean bien
    with open(os.path.join(root, PAIRS_FILE), "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["image", "background"])
        for image in sorted(pairs):
            w.writerow([image, pairs[image]])


def _relative(path, root):
    return os.path.relpath(path, root).replace(os.sep, "/")


def link_background(image_path, background_path, root=config.DATASET_DIR):
    pairs = _read_pairs(root)
    pairs[_relative(image_path, root)] = _relative(background_path, root)
    _write_pairs(pairs, root)


def unlink_background(image_path, root=config.DATASET_DIR):
    pairs = _read_pairs(root)
    if pairs.pop(_relative(image_path, root), None) is not None:
        _write_pairs(pairs, root)


def background_for(image_path, root=config.DATASET_DIR):
    bg = _read_pairs(root).get(_relative(image_path, root))
    if bg is None:
        return None
    return cv2.imread(os.path.join(root, bg))
