# panel con las imagenes de referencia de H, O, L, A juntas (paso 1 y para el informe)
#   python -m lse_auth.reference_viewer [--no-show]

import argparse
import os

import cv2
import numpy as np

from lse_auth import config
from lse_auth.alphabet import LETTERS, UNLOCK_SEQUENCE

TILE_SIZE = 320
HEADER_HEIGHT = 50
OUTPUT_FILE = os.path.join(config.REFERENCE_DIR, "panel_HOLA.png")


def make_tile(image, title):
    # cuadrado manteniendo la proporcion, blanco alrededor y la letra arriba
    h, w = image.shape[:2]
    s = TILE_SIZE / max(h, w)
    small = cv2.resize(image, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
    canvas = np.full((TILE_SIZE, TILE_SIZE, 3), 255, dtype=np.uint8)
    y0 = (TILE_SIZE - small.shape[0]) // 2
    x0 = (TILE_SIZE - small.shape[1]) // 2
    canvas[y0:y0 + small.shape[0], x0:x0 + small.shape[1]] = small

    header = np.full((HEADER_HEIGHT, TILE_SIZE, 3), 255, dtype=np.uint8)
    cv2.putText(header, title, (10, 36), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 0, 0), 2, cv2.LINE_AA)
    return np.vstack([header, canvas])


def build_panel():
    tiles = []
    for i, letter in enumerate(UNLOCK_SEQUENCE, start=1):
        path = os.path.join(config.REFERENCE_DIR, LETTERS[letter].reference_image)
        img = cv2.imread(path)
        if img is None:
            raise FileNotFoundError(f"Reference image not found: {path}")
        tiles.append(make_tile(img, f"{i}. {letter}"))

    sep = np.full((tiles[0].shape[0], 4, 3), 200, dtype=np.uint8)
    row = [tiles[0]]
    for t in tiles[1:]:
        row += [sep, t]
    return np.hstack(row)


def main():
    parser = argparse.ArgumentParser(description="Show the H-O-L-A reference panel.")
    parser.add_argument("--no-show", action="store_true",
                        help="save the panel without opening a window")
    args = parser.parse_args()

    panel = build_panel()
    cv2.imwrite(OUTPUT_FILE, panel)
    print(f"Panel saved to {OUTPUT_FILE}")
    for letter in UNLOCK_SEQUENCE:
        print(f"  {letter}: {LETTERS[letter].description}")

    if not args.no_show:
        cv2.imshow("LSE reference: H-O-L-A", panel)
        cv2.waitKey()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
