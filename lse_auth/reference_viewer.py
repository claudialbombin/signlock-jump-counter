"""
Build a single panel with the reference image of every target letter.

Step 1 asks to review the reference pictures before implementing the
classifier. Instead of opening four files every time, this script puts them
side by side, in unlock order (H, O, L, A), with the letter on top. The panel
is also handy for the report.

Usage
-----
    python -m lse_auth.reference_viewer            # show and save the panel
    python -m lse_auth.reference_viewer --no-show  # only save it
"""

import argparse
import os
from typing import List

import cv2
import numpy as np

from lse_auth import config
from lse_auth.alphabet import LETTERS, UNLOCK_SEQUENCE

TILE_SIZE = 320          # every reference image is resized to a square tile
HEADER_HEIGHT = 50       # white strip on top of each tile for the letter
OUTPUT_FILE = os.path.join(config.REFERENCE_DIR, "panel_HOLA.png")


def make_tile(image: np.ndarray, title: str) -> np.ndarray:
    """
    Fit an image into a square tile (keeping its aspect ratio) and add a title.

    Parameters
    ----------
    image : np.ndarray
        BGR image of any size.
    title : str
        Text written in the header of the tile.

    Returns
    -------
    np.ndarray
        BGR tile of shape (HEADER_HEIGHT + TILE_SIZE, TILE_SIZE, 3).
    """
    h, w = image.shape[:2]
    scale = TILE_SIZE / max(h, w)
    resized = cv2.resize(image, (int(w * scale), int(h * scale)),
                         interpolation=cv2.INTER_AREA)

    # Paste the resized image centred on a white canvas (letterbox)
    canvas = np.full((TILE_SIZE, TILE_SIZE, 3), 255, dtype=np.uint8)
    y0 = (TILE_SIZE - resized.shape[0]) // 2
    x0 = (TILE_SIZE - resized.shape[1]) // 2
    canvas[y0:y0 + resized.shape[0], x0:x0 + resized.shape[1]] = resized

    header = np.full((HEADER_HEIGHT, TILE_SIZE, 3), 255, dtype=np.uint8)
    cv2.putText(header, title, (10, 36), cv2.FONT_HERSHEY_SIMPLEX, 1.1,
                (0, 0, 0), 2, cv2.LINE_AA)
    return np.vstack([header, canvas])


def build_panel() -> np.ndarray:
    """
    Load the reference image of each letter and concatenate them horizontally.

    Returns
    -------
    np.ndarray
        BGR panel with one tile per letter, in unlock order.
    """
    tiles: List[np.ndarray] = []
    for position, letter in enumerate(UNLOCK_SEQUENCE, start=1):
        path = os.path.join(config.REFERENCE_DIR, LETTERS[letter].reference_image)
        image = cv2.imread(path)
        if image is None:
            raise FileNotFoundError(f"Reference image not found: {path}")
        tiles.append(make_tile(image, f"{position}. {letter}"))

    # Thin grey separator between tiles so they don't blend together
    separator = np.full((tiles[0].shape[0], 4, 3), 200, dtype=np.uint8)
    row = [tiles[0]]
    for tile in tiles[1:]:
        row += [separator, tile]
    return np.hstack(row)


def main() -> None:
    parser = argparse.ArgumentParser(description="Show the H-O-L-A reference panel.")
    parser.add_argument("--no-show", action="store_true",
                        help="save the panel without opening a window")
    args = parser.parse_args()

    panel = build_panel()
    cv2.imwrite(OUTPUT_FILE, panel)
    print(f"Panel saved to {OUTPUT_FILE}")

    # Print the written description too, so the panel and the rules are
    # always read together
    for letter in UNLOCK_SEQUENCE:
        print(f"  {letter}: {LETTERS[letter].description}")

    if not args.no_show:
        cv2.imshow("LSE reference: H-O-L-A", panel)
        cv2.waitKey()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
