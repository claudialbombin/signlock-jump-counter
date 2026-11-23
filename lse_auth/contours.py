"""
Step 4 - From the hand mask to one clean contour.

segment_hand (step 3) may leave small blobs next to the hand (e.g. the edge
of the shelf). Here we keep only the biggest connected component, extract
its outer contour and its holes, and locate the palm:

* The palm centre is the point of the hand farthest from the background
  (maximum of the distance transform) and that distance is the palm
  radius. Fingers are thin, so they never win against the palm. This is
  much more stable than the centroid, which moves towards the arm or the
  extended fingers.
* The holes are kept (bigger than MIN_HOLE_AREA): one of them may be the
  circle of the O (thumb touching the index finger). Whether it really is
  the O circle is decided in features.py, relative to the palm.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple

import cv2
import numpy as np

from lse_auth import config

MIN_HAND_AREA = 8000     # px at 1280x720; smaller blobs are noise, not a hand
MIN_HOLE_AREA = 100      # px; smaller holes are noise (the size that matters
                         # is judged later relative to the palm, in features.py)


@dataclass
class HandContour:
    """Everything the next steps need to know about the hand silhouette."""

    contour: np.ndarray                  # outer contour, (N, 1, 2) int32
    bbox: Tuple[int, int, int, int]      # x, y, w, h
    area: float                          # area of the outer contour
    holes: List[np.ndarray]              # contours of the holes (O circle, gaps)
    palm_center: Tuple[int, int]         # x, y of the distance-transform max
    palm_radius: float                   # distance from the palm centre to the border
    roi: Tuple[int, int, int, int]       # ROI the mask was cut to (x, y, w, h)

    @property
    def has_hole(self) -> bool:
        return bool(self.holes)

    def touches_roi_border(self, point: Tuple[int, int], margin: int = 4) -> bool:
        """True if the point lies on the edge of the ROI (the shape is cut there)."""
        x, y, w, h = self.roi
        px, py = point
        return (px - x < margin or x + w - 1 - px < margin
                or py - y < margin or y + h - 1 - py < margin)


def find_hand_contour(mask: np.ndarray, min_area: int = MIN_HAND_AREA,
                      roi: Optional[Tuple[int, int, int, int]] = None) -> Optional[HandContour]:
    """
    Keep the biggest blob of the mask and describe it.

    Parameters
    ----------
    mask : np.ndarray
        Binary uint8 mask from segment_hand (255 = hand).
    min_area : int
        Minimum area in pixels to accept the blob as a hand.
    roi : tuple of int, optional
        ROI used by segment_hand. By default config.HAND_ROI.

    Returns
    -------
    HandContour or None
        None when there is no blob big enough (empty ROI).
    """
    # Work only on the bounding box of the non-zero pixels (the ROI): the
    # distance transform of the full 1280x720 frame would be ~4x slower.
    mask_shape = mask.shape
    ox, oy, bw, bh = cv2.boundingRect(mask)
    if bw == 0 or bh == 0:
        return None
    mask = mask[oy:oy + bh, ox:ox + bw]

    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    if n < 2:
        return None
    biggest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    if stats[biggest, cv2.CC_STAT_AREA] < min_area:
        return None
    hand = np.where(labels == biggest, 255, 0).astype(np.uint8)

    # RETR_CCOMP: two levels, outer contours and their holes
    contours, hierarchy = cv2.findContours(hand, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE,
                                           offset=(ox, oy))
    outer = max((c for c, h in zip(contours, hierarchy[0]) if h[3] < 0),
                key=cv2.contourArea)
    holes = [c for c, h in zip(contours, hierarchy[0])
             if h[3] >= 0 and cv2.contourArea(c) > MIN_HOLE_AREA]

    distance = cv2.distanceTransform(hand, cv2.DIST_L2, 5)
    _, radius, _, (cx, cy) = cv2.minMaxLoc(distance)
    center = (cx + ox, cy + oy)          # back to full-frame coordinates

    return HandContour(contour=outer, bbox=cv2.boundingRect(outer),
                       area=cv2.contourArea(outer), holes=holes,
                       palm_center=center, palm_radius=float(radius),
                       roi=roi if roi is not None else
                       config.roi_pixels(mask_shape[1], mask_shape[0]))
