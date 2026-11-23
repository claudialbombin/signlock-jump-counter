"""
Step 5 - Geometric features of the hand silhouette.

The main feature is the list of extended fingers, found as fingertips on
the outer contour:

* A fingertip is a contour point whose distance to the palm centre is a
  local maximum and is larger than TIP_FACTOR times the palm radius
  (a bent finger stays close to the palm, an extended one does not).
* Tips closer than TIP_MERGE palm radii to each other are the same finger.
* Tips on the edge of the ROI are discarded: the shape is cut there, so it
  is not the end of a finger (it happens with the arm, or with a strip of
  wall when the camera moved after saving the background). If the hand
  leaves the ROI above the palm, `cut` is set and the classifier gives up.
* A short tip (1.7-2.0 palm radii) or a tip pointing below the horizontal
  (> 180 deg) is only kept when it is thin: that is a thumb held close to
  the hand or held low. Knuckles, the O circle and the corner of the
  wrist are just as short / low but much wider (1.1-1.5 palm radii).
* Each finger gets
    - an angle in degrees measured like in maths, on the image as it is
      shown (mirrored): 0 = pointing right, 90 = up, 180 = left. Tips
      pointing down (the wrist / forearm leaving the ROI) are discarded.
    - a width: distance between the two contour points that are
      WIDTH_ARC palm radii away from the tip along the contour, one on
      each side. Walking along the contour follows the finger even when it
      is not pointing at the palm centre. Measured on the dataset, relative
      to the palm radius: one finger 0.36-0.63, the curled thumb-index
      circle of the O ~1.46. Two fingers pressed together (H) look like a
      single finger twice as wide, which is why the width matters.
    - a length: distance tip - palm centre, in palm radii.

Everything is divided by the palm radius, so the features do not depend on
how far the hand is from the camera.

For the A (closed fist, no finger) two more numbers matter:
* solidity: area / convex hull area. A fist is compact (0.78-0.85).
* top_extent: how far the silhouette reaches above the palm centre (contour
  points between 20 and 160 deg), in palm radii. In a fist the knuckles are
  right on top of the palm (1.22-1.51); an open hand whose fingers are not
  found (pressed together or blurred by movement) still reaches 1.58+.
The aspect ratio of the bounding box is kept for reference.
"""

import math
from dataclasses import dataclass, field
from typing import List, Tuple

import cv2
import numpy as np

from lse_auth.contours import HandContour

TIP_FACTOR = 2.0           # fingertip if farther than 2 palm radii from the centre
SHORT_TIP_FACTOR = 1.7     # a short thumb (1.7-2.0 radii) is accepted if it is thin:
SHORT_TIP_MAX_WIDTH = 0.8  # knuckles and the O circle are short but wide (1.1-1.5)
TIP_MERGE = 0.5            # tips closer than half a palm radius are one finger
MIN_TIP_ANGLE = -30.0      # tips below this angle point down: wrist or forearm
MAX_TIP_ANGLE = 220.0      # a thumb held low points to ~195; the forearm leaves through the ROI bottom (border tips are dropped)
WIDTH_ARC = 1.0            # arc length (palm radii) from the tip where the width is taken

# The circle of the O: a hole on the thumb side of the palm (upper-left in
# the mirrored image) and not tiny. Measured: O circle 0.12-0.25 palm
# radii^2 at 139-150 deg; false gaps in an H 0.01-0.05 at ~-145 deg.
O_HOLE_MIN_AREA = 0.08     # in palm radii squared
O_HOLE_ANGLES = (90.0, 200.0)


@dataclass
class Finger:
    """One extended finger (or several pressed together)."""

    tip: Tuple[int, int]
    angle: float          # degrees, 0 right, 90 up, 180 left
    width: float          # in palm radii
    length: float         # tip to palm centre, in palm radii


@dataclass
class HandFeatures:
    """Numbers the rule-based classifier (step 6) looks at."""

    fingers: List[Finger] = field(default_factory=list)       # sorted by angle
    cut: bool = False               # the hand leaves the ROI above the palm
    has_hole: bool = False          # any hole at all
    o_hole: bool = False            # a hole that looks like the O circle
    solidity: float = 0.0
    aspect_ratio: float = 0.0       # bbox width / height
    top_extent: float = 0.0         # reach above the palm centre, palm radii

    @property
    def n_fingers(self) -> int:
        return len(self.fingers)

    @property
    def finger_angles(self) -> List[float]:
        return [f.angle for f in self.fingers]

    @property
    def fingertips(self) -> List[Tuple[int, int]]:
        return [f.tip for f in self.fingers]


def _tip_angle(center: Tuple[int, int], tip: Tuple[float, float]) -> float:
    """Angle of the vector palm centre -> tip, y axis pointing up."""
    angle = math.degrees(math.atan2(center[1] - tip[1], tip[0] - center[0]))
    # map to (-90, 270] so that "left" is ~180 and not -180
    return angle + 360 if angle <= -90 else angle


def find_fingers(hand: HandContour) -> List[Finger]:
    """Extended fingers of the hand, sorted by angle."""
    points = hand.contour[:, 0, :].astype(np.float32)
    n = len(points)
    cx, cy = hand.palm_center
    radius = hand.palm_radius
    dist = np.hypot(points[:, 0] - cx, points[:, 1] - cy).astype(np.float32)
    window = max(5, n // 60)        # neighbourhood for the local maximum

    # Local maxima of the distance along the (closed) contour
    # (grey dilation = running maximum, much faster than a Python loop)
    padded = np.concatenate([dist[-window:], dist, dist[:window]])
    running_max = cv2.dilate(padded.reshape(1, -1),
                             np.ones((1, 2 * window + 1), np.uint8))[0, window:-window]
    candidates = np.where((dist >= running_max) & (dist > SHORT_TIP_FACTOR * radius))[0]

    # Cumulative arc length, to measure the width at a fixed distance from the tip
    steps = np.hypot(*np.diff(np.vstack([points, points[:1]]), axis=0).T)
    arc = np.concatenate([[0.0], np.cumsum(steps)[:-1]])
    perimeter = float(steps.sum())

    def point_at(i: int, offset: float) -> np.ndarray:
        j = int(np.searchsorted(arc, (arc[i] + offset) % perimeter)) % n
        return points[j]

    fingers: List[Finger] = []
    for i in candidates[np.argsort(-dist[candidates])]:      # farthest first
        p = points[i]
        if any(math.hypot(p[0] - f.tip[0], p[1] - f.tip[1]) < TIP_MERGE * radius
               for f in fingers):
            continue
        angle = _tip_angle(hand.palm_center, p)
        if not MIN_TIP_ANGLE <= angle <= MAX_TIP_ANGLE:
            continue
        if hand.touches_roi_border((int(p[0]), int(p[1]))):
            continue
        offset = WIDTH_ARC * radius
        width = float(np.linalg.norm(point_at(i, offset) - point_at(i, -offset)))
        # Short tips and tips pointing below the horizontal must be thin:
        # a thumb is, knuckles, the O circle and the wrist corner are not.
        if ((dist[i] < TIP_FACTOR * radius or angle > 180.0)
                and width > SHORT_TIP_MAX_WIDTH * radius):
            continue
        fingers.append(Finger(tip=(int(p[0]), int(p[1])), angle=round(angle, 1),
                              width=round(width / radius, 2),
                              length=round(float(dist[i]) / radius, 2)))
    return sorted(fingers, key=lambda f: f.angle)


def is_cut(hand: HandContour) -> bool:
    """
    True if the silhouette touches the ROI edge above the palm centre.

    The forearm always leaves the ROI through the bottom, which is fine;
    anything leaving through the top or the sides above the palm is a
    finger cut by the box, and the hand cannot be read reliably.
    """
    x, y, w, h = hand.roi
    pts = hand.contour[:, 0, :]
    above = pts[pts[:, 1] < hand.palm_center[1]]
    margin = 4
    on_border = ((above[:, 0] - x < margin) | (x + w - 1 - above[:, 0] < margin)
                 | (above[:, 1] - y < margin))
    return bool(on_border.any())


def is_o_circle(hand: HandContour) -> bool:
    """True if one of the holes has the size and position of the O circle."""
    r2 = hand.palm_radius ** 2
    for hole in hand.holes:
        m = cv2.moments(hole)
        if m["m00"] == 0 or cv2.contourArea(hole) < O_HOLE_MIN_AREA * r2:
            continue
        angle = _tip_angle(hand.palm_center, (m["m10"] / m["m00"], m["m01"] / m["m00"]))
        if O_HOLE_ANGLES[0] <= angle <= O_HOLE_ANGLES[1]:
            return True
    return False


TOP_ANGLES = (20.0, 160.0)   # "above the palm" for top_extent


def top_extent(hand: HandContour) -> float:
    """Farthest contour point above the palm centre, in palm radii."""
    pts = hand.contour[:, 0, :].astype(np.float32)
    cx, cy = hand.palm_center
    angles = np.degrees(np.arctan2(cy - pts[:, 1], pts[:, 0] - cx))
    dist = np.hypot(pts[:, 0] - cx, pts[:, 1] - cy)
    above = dist[(angles >= TOP_ANGLES[0]) & (angles <= TOP_ANGLES[1])]
    return float(above.max() / hand.palm_radius) if len(above) else 0.0


def extract_features(hand: HandContour) -> HandFeatures:
    """Compute every feature of one hand silhouette."""
    hull_area = cv2.contourArea(cv2.convexHull(hand.contour))
    _, _, w, h = hand.bbox
    return HandFeatures(
        fingers=find_fingers(hand),
        cut=is_cut(hand),
        has_hole=hand.has_hole,
        o_hole=is_o_circle(hand),
        solidity=hand.area / hull_area if hull_area else 0.0,
        aspect_ratio=w / h if h else 0.0,
        top_extent=round(top_extent(hand), 2),
    )
