"""
Step 5 - Geometric features of the hand silhouette.

The main feature is the list of extended fingers, found as fingertips on
the outer contour:

* A fingertip is a contour point whose distance to the palm centre is a
  local maximum and is larger than TIP_FACTOR times the palm radius
  (a bent finger stays close to the palm, an extended one does not).
* Tips closer than one palm radius to each other are the same finger.
* Each fingertip gets an angle in degrees measured like in maths, on the
  image as it is shown (mirrored): 0 = pointing right, 90 = up,
  180 = left. Tips pointing down (the wrist / forearm leaving the ROI)
  are discarded.

With the right hand, palm to the camera, the letters look like this:

    L  2 fingers: index up (~90 deg) + thumb to the left (~160 deg)
    H  3 fingers: index + middle together to the right (~20 and ~45 deg)
       + thumb up-left (~115 deg)
    O  3 free fingers (~20, ~55, ~78 deg) + the thumb-index circle
       (4th tip at ~138 deg) + its hole

Solidity (area / convex hull area) and aspect ratio are kept too: they
will help with A (closed fist, high solidity) once its images are valid.
"""

import math
from dataclasses import dataclass, field
from typing import List, Tuple

import cv2
import numpy as np

from lse_auth.contours import HandContour

TIP_FACTOR = 2.0           # fingertip if farther than 2 palm radii from the centre
MIN_TIP_ANGLE = -30.0      # tips below this angle point down: wrist or forearm
MAX_TIP_ANGLE = 195.0      # the forearm entering from the bottom-left is at ~205


@dataclass
class HandFeatures:
    """Numbers the rule-based classifier (step 6) looks at."""

    finger_angles: List[float] = field(default_factory=list)   # sorted, degrees
    fingertips: List[Tuple[int, int]] = field(default_factory=list)
    has_hole: bool = False
    solidity: float = 0.0
    aspect_ratio: float = 0.0       # bbox width / height

    @property
    def n_fingers(self) -> int:
        return len(self.finger_angles)


def _tip_angle(center: Tuple[int, int], tip: Tuple[float, float]) -> float:
    """Angle of the vector palm centre -> tip, y axis pointing up."""
    angle = math.degrees(math.atan2(center[1] - tip[1], tip[0] - center[0]))
    # map to (-90, 270] so that "left" is ~180 and not -180
    return angle + 360 if angle <= -90 else angle


def find_fingertips(hand: HandContour) -> List[Tuple[Tuple[int, int], float]]:
    """
    Fingertips of the hand as (point, angle) pairs, sorted by angle.
    """
    points = hand.contour[:, 0, :].astype(np.float32)
    cx, cy = hand.palm_center
    dist = np.hypot(points[:, 0] - cx, points[:, 1] - cy).astype(np.float32)
    n = len(points)
    window = max(5, n // 60)        # neighbourhood for the local maximum

    # Local maxima of the distance along the (closed) contour
    padded = np.concatenate([dist[-window:], dist, dist[:window]])
    # (grey dilation = running maximum, much faster than a Python loop)
    running_max = cv2.dilate(padded.reshape(1, -1),
                             np.ones((1, 2 * window + 1), np.uint8))[0, window:-window]
    local_max = dist >= running_max
    candidates = np.where(local_max & (dist > TIP_FACTOR * hand.palm_radius))[0]

    tips: List[Tuple[Tuple[int, int], float]] = []
    for i in candidates[np.argsort(-dist[candidates])]:      # farthest first
        p = points[i]
        if any(math.hypot(p[0] - q[0], p[1] - q[1]) < hand.palm_radius
               for q, _ in tips):
            continue
        angle = _tip_angle(hand.palm_center, p)
        if MIN_TIP_ANGLE <= angle <= MAX_TIP_ANGLE:
            tips.append(((int(p[0]), int(p[1])), angle))
    return sorted(tips, key=lambda t: t[1])


def extract_features(hand: HandContour) -> HandFeatures:
    """Compute every feature of one hand silhouette."""
    tips = find_fingertips(hand)
    hull_area = cv2.contourArea(cv2.convexHull(hand.contour))
    _, _, w, h = hand.bbox
    return HandFeatures(
        finger_angles=[round(a, 1) for _, a in tips],
        fingertips=[p for p, _ in tips],
        has_hole=hand.has_hole,
        solidity=hand.area / hull_area if hull_area else 0.0,
        aspect_ratio=w / h if h else 0.0,
    )
