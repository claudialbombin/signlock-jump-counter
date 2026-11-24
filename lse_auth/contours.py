# paso 4: de la mascara a un contorno + centro de la palma
import cv2
import numpy as np

from lse_auth import config

MIN_HAND_AREA = 8000
MIN_HOLE_AREA = 100


class HandContour:
    def __init__(self, contour, bbox, area, holes, palm_center, palm_radius, roi):
        self.contour = contour
        self.bbox = bbox
        self.area = area
        self.holes = holes
        self.palm_center = palm_center
        self.palm_radius = palm_radius
        self.roi = roi

    @property
    def has_hole(self):
        return len(self.holes) > 0

    def touches_roi_border(self, point, margin=4):
        x, y, w, h = self.roi
        px, py = point
        return (px - x < margin or x + w - 1 - px < margin
                or py - y < margin or y + h - 1 - py < margin)


def find_hand_contour(mask, min_area=MIN_HAND_AREA, roi=None):
    if roi is None:
        roi = config.roi_pixels(mask.shape[1], mask.shape[0])

    # recortar a la zona con pixeles, el distanceTransform de todo el frame tardaba 4 veces mas
    ox, oy, bw, bh = cv2.boundingRect(mask)
    if bw == 0 or bh == 0:
        return None
    mask = mask[oy:oy + bh, ox:ox + bw]

    # nos quedamos con el blob mas grande
    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    if n < 2:
        return None
    big = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
    if stats[big, cv2.CC_STAT_AREA] < min_area:
        return None
    hand = np.uint8(labels == big) * 255

    contours, hier = cv2.findContours(hand, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE, offset=(ox, oy))
    outer = None
    holes = []
    for c, h in zip(contours, hier[0]):
        if h[3] < 0:
            if outer is None or cv2.contourArea(c) > cv2.contourArea(outer):
                outer = c
        elif cv2.contourArea(c) > MIN_HOLE_AREA:
            holes.append(c)   # puede ser el circulo de la O

    # centro de la palma = punto mas lejos del fondo (mas estable que el centroide)
    dist = cv2.distanceTransform(hand, cv2.DIST_L2, 5)
    _, radius, _, (cx, cy) = cv2.minMaxLoc(dist)

    return HandContour(outer, cv2.boundingRect(outer), cv2.contourArea(outer), holes,
                       (cx + ox, cy + oy), float(radius), roi)
