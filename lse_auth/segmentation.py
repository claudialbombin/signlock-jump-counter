"""
Step 3 - Isolate the hand inside the ROI.

Why not only skin colour?
    With the first dataset the wooden shelf and the warm-lit wall had the
    same Cr/Cb values as pale skin, so a colour threshold alone kept them.
    Here the hand is found as "what changed with respect to the empty scene
    AND looks like skin":

    1. Background model: average of a few frames of the empty scene.
    2. Exposure compensation: the webcam changes its exposure and white
       balance on its own when a hand comes in, so the whole picture gets
       brighter. A brightness transfer function (one look-up table per BGR
       channel, Javed et al. 2005) maps the background to the current
       light before comparing.
    3. Background subtraction in YCrCb with less weight on Y (shadows and
       exposure mostly change luminance).
    4. The "changed" mask is closed and its holes filled, so the palm has
       no gaps even where it looks like the wall behind it.
    5. Intersection with a wide skin range: this removes the sleeve, the
       bracelet and, importantly, the wall seen through the O, so the hole
       of the O survives.
    6. Opening + closing to clean the borders.

Everything is computed only inside the ROI (config.HAND_ROI), which also
makes it fast. The returned mask has the size of the full frame.
"""

from typing import Dict, Optional, Tuple

import cv2
import numpy as np

from lse_auth import config


def _ellipse(size: int) -> np.ndarray:
    """Elliptic structuring element of the given size."""
    return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (size, size))


class BackgroundModel:
    """
    Average of the first frames of the empty scene.

    Usage in a live loop::

        model = BackgroundModel()
        while not model.ready:
            model.add(cam.read())
        background = model.image

    Call reset() (e.g. with a key) when the light changes or the camera
    moves, and feed it again with the ROI empty.
    """

    def __init__(self, n_frames: int = config.BG_FRAMES) -> None:
        self.n_frames = n_frames
        self.reset()

    def reset(self) -> None:
        """Forget the current background and start averaging again."""
        self._sum: Optional[np.ndarray] = None
        self._count = 0
        self.image: Optional[np.ndarray] = None

    @property
    def ready(self) -> bool:
        """True once n_frames have been averaged."""
        return self.image is not None

    def add(self, frame: np.ndarray) -> bool:
        """
        Add one frame of the empty scene.

        Returns
        -------
        bool
            True when the background is complete.
        """
        if self.ready:
            return True
        if self._sum is None:
            self._sum = np.zeros(frame.shape, np.float32)
        self._sum += frame
        self._count += 1
        if self._count >= self.n_frames:
            self.image = (self._sum / self._count).round().astype(np.uint8)
            self._sum = None
        return self.ready


def match_brightness(background: np.ndarray, frame: np.ndarray,
                     bin_size: int = 8, step: int = 8,
                     min_pixels: int = 50) -> np.ndarray:
    """
    Map the background to the current exposure of the frame.

    For each BGR channel the background values are grouped in bins and,
    for every bin, the median value of the same pixels in the current
    frame is taken (vectorised with one sort per channel). Interpolating those medians gives a look-up table
    (brightness transfer function) that is applied to the background.
    The median ignores the pixels covered by the hand as long as the hand
    is less than half of each bin, which holds because most of the ROI is
    still background.

    Parameters
    ----------
    background, frame : np.ndarray
        BGR images of the same size (usually the ROI crops).
    bin_size : int
        Width of the intensity bins.
    step : int
        Subsampling of the pixels used to estimate the table (speed).
    min_pixels : int
        Bins with fewer sampled pixels are ignored.

    Returns
    -------
    np.ndarray
        Background with the brightness of the frame.
    """
    matched = np.empty_like(background)
    levels = np.arange(256)
    for ch in range(3):
        bg_values = background[::step, ::step, ch].ravel()
        fr_values = frame[::step, ::step, ch].ravel()
        bins = (bg_values // bin_size).astype(np.int32)
        counts = np.bincount(bins, minlength=256 // bin_size)
        # Median of the frame values of each bin without a Python loop:
        # sort by (bin, frame value) and take the middle element of each bin.
        ordered = np.sort(bins * 256 + fr_values.astype(np.int32))
        starts = np.cumsum(counts) - counts
        valid = np.where(counts >= min_pixels)[0]
        ys = ordered[starts[valid] + counts[valid] // 2] - valid * 256
        # Background value of each bin: its mean (inside a narrow bin the
        # mean and the median are practically the same)
        xs = np.bincount(bins, weights=bg_values, minlength=len(counts))[valid] / counts[valid]
        if len(xs) < 2:            # not enough information: leave it as is
            matched[..., ch] = background[..., ch]
            continue
        lut = np.clip(np.interp(levels, xs, ys), 0, 255).astype(np.uint8)
        matched[..., ch] = cv2.LUT(background[..., ch], lut)
    return matched


def _fill_holes(mask: np.ndarray) -> np.ndarray:
    """Fill the holes of a binary mask (flood fill from the border)."""
    h, w = mask.shape
    padded = np.zeros((h + 2, w + 2), np.uint8)
    padded[1:-1, 1:-1] = mask
    flood = padded.copy()
    cv2.floodFill(flood, np.zeros((h + 4, w + 4), np.uint8), (0, 0), 255)
    holes = cv2.bitwise_not(flood)[1:-1, 1:-1]
    return cv2.bitwise_or(mask, holes)


def segment_hand(frame: np.ndarray, background: np.ndarray,
                 roi: Optional[Tuple[int, int, int, int]] = None,
                 debug: bool = False):
    """
    Binary mask of the hand.

    Parameters
    ----------
    frame : np.ndarray
        Current BGR frame (undistorted and mirrored, like the background).
    background : np.ndarray
        BGR image of the empty scene, same size and same camera position.
    roi : tuple of int, optional
        (x, y, w, h) in pixels. By default config.HAND_ROI.
    debug : bool
        If True also return the intermediate masks (for the figure of the
        "image transformation sequence" of the report).

    Returns
    -------
    np.ndarray
        uint8 mask of the full frame size, 255 = hand, 0 outside the ROI.
    dict, only if debug
        Crops of the ROI: "frame", "background", "matched", "score",
        "changed", "changed_filled", "skin", "mask".
    """
    if frame.shape != background.shape:
        raise ValueError("frame and background must have the same size "
                         f"({frame.shape} vs {background.shape})")
    h_img, w_img = frame.shape[:2]
    x, y, w, h = roi if roi is not None else config.roi_pixels(w_img, h_img)
    fr = frame[y:y + h, x:x + w]
    bg = background[y:y + h, x:x + w]

    # 1-2. Background with the current exposure
    matched = match_brightness(bg, fr)

    # 3. Difference in YCrCb, less weight on luminance
    fr_ycc = cv2.cvtColor(fr, cv2.COLOR_BGR2YCrCb)
    bg_ycc = cv2.cvtColor(matched, cv2.COLOR_BGR2YCrCb)
    diff = cv2.absdiff(fr_ycc, bg_ycc).astype(np.float32)
    score = (config.BG_WEIGHT_Y * diff[..., 0] + diff[..., 1] + diff[..., 2])
    score = cv2.GaussianBlur(score, (5, 5), 0)
    changed = np.where(score > config.BG_THRESHOLD, 255, 0).astype(np.uint8)

    # 4. Whole silhouette of what changed (palm without gaps). The big
    #    closing is done at half resolution (4 times fewer pixels, same
    #    result once intersected with the skin mask at full resolution).
    small = cv2.resize(changed, (w // 2, h // 2), interpolation=cv2.INTER_NEAREST)
    small = cv2.morphologyEx(small, cv2.MORPH_CLOSE,
                             _ellipse(config.FG_CLOSE_KERNEL // 2 | 1))
    small = _fill_holes(small)
    changed_filled = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)

    # 5. Keep only skin (removes sleeve, bracelet and the wall inside the O)
    skin = cv2.inRange(fr_ycc, config.SKIN_LOWER, config.SKIN_UPPER)
    hand = cv2.bitwise_and(changed_filled, skin)

    # 6. Clean
    hand = cv2.morphologyEx(hand, cv2.MORPH_OPEN, _ellipse(config.OPEN_KERNEL))
    hand = cv2.morphologyEx(hand, cv2.MORPH_CLOSE, _ellipse(config.CLOSE_KERNEL))

    mask = np.zeros((h_img, w_img), np.uint8)
    mask[y:y + h, x:x + w] = hand
    if not debug:
        return mask

    steps: Dict[str, np.ndarray] = {
        "frame": fr, "background": bg, "matched": matched,
        "score": np.clip(score * 4, 0, 255).astype(np.uint8),
        "changed": changed, "changed_filled": changed_filled,
        "skin": skin, "mask": hand,
    }
    return mask, steps
