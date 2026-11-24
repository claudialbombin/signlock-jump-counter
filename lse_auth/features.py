# paso 5: caracteristicas de la silueta
# todo va dividido por el radio de la palma para que no dependa de la distancia

import math

import cv2
import numpy as np

TIP_FACTOR = 2.0           # punta si esta a mas de 2 radios del centro
SHORT_TIP_FACTOR = 1.7     # pulgar pegado: mas corto, pero solo si es fino
SHORT_TIP_MAX_WIDTH = 0.8  # nudillos y circulo de la O son cortos pero anchos (1.1-1.5)
TIP_MERGE = 0.5
MIN_TIP_ANGLE = -30.0      # por debajo es la muñeca
MAX_TIP_ANGLE = 220.0      # pulgar bajo ~195
WIDTH_ARC = 1.0

# circulo de la O: medido 0.12-0.25 r^2 a 139-150 grados
# (los huecos falsos de la H son 0.01-0.05 a -145)
O_HOLE_MIN_AREA = 0.08
O_HOLE_ANGLES = (90.0, 200.0)
TOP_ANGLES = (20.0, 160.0)


class Finger:
    def __init__(self, tip, angle, width, length):
        self.tip = tip
        self.angle = angle      # 0 derecha, 90 arriba, 180 izq
        self.width = width
        self.length = length

    def __repr__(self):
        return f"Finger(tip={self.tip}, angle={self.angle}, width={self.width}, length={self.length})"


class HandFeatures:
    def __init__(self, fingers=None, cut=False, has_hole=False, o_hole=False,
                 solidity=0.0, aspect_ratio=0.0, top_extent=0.0):
        self.fingers = fingers if fingers is not None else []
        self.cut = cut              # la mano se sale del recuadro por arriba
        self.has_hole = has_hole
        self.o_hole = o_hole
        self.solidity = solidity
        self.aspect_ratio = aspect_ratio
        self.top_extent = top_extent

    @property
    def n_fingers(self):
        return len(self.fingers)

    @property
    def finger_angles(self):
        return [f.angle for f in self.fingers]

    @property
    def fingertips(self):
        return [f.tip for f in self.fingers]


def _tip_angle(center, tip):
    a = math.degrees(math.atan2(center[1] - tip[1], tip[0] - center[0]))
    if a <= -90:
        a += 360   # que la izquierda sea 180 y no -180
    return a


def find_fingers(hand):
    pts = hand.contour[:, 0, :].astype(np.float32)
    n = len(pts)
    cx, cy = hand.palm_center
    r = hand.palm_radius
    dist = np.hypot(pts[:, 0] - cx, pts[:, 1] - cy).astype(np.float32)
    win = max(5, n // 60)

    # maximos locales de la distancia al centro (dilate = maximo movil, mucho
    # mas rapido que recorrer el contorno)
    padded = np.concatenate([dist[-win:], dist, dist[:win]])
    local_max = cv2.dilate(padded.reshape(1, -1), np.ones((1, 2 * win + 1), np.uint8))[0, win:-win]
    cand = np.where((dist >= local_max) & (dist > SHORT_TIP_FACTOR * r))[0]

    # longitud de arco para medir el ancho a una distancia fija de la punta
    seg = np.hypot(*np.diff(np.vstack([pts, pts[:1]]), axis=0).T)
    arc = np.concatenate([[0.0], np.cumsum(seg)[:-1]])
    perim = float(seg.sum())

    def point_at(i, offset):
        j = int(np.searchsorted(arc, (arc[i] + offset) % perim)) % n
        return pts[j]

    fingers = []
    for i in cand[np.argsort(-dist[cand])]:
        p = pts[i]
        repeated = False
        for f in fingers:
            if math.hypot(p[0] - f.tip[0], p[1] - f.tip[1]) < TIP_MERGE * r:
                repeated = True
                break
        if repeated:
            continue
        angle = _tip_angle(hand.palm_center, p)
        if angle < MIN_TIP_ANGLE or angle > MAX_TIP_ANGLE:
            continue
        # en el borde del recuadro la forma esta cortada, no es una punta
        if hand.touches_roi_border((int(p[0]), int(p[1]))):
            continue
        width = float(np.linalg.norm(point_at(i, WIDTH_ARC * r) - point_at(i, -WIDTH_ARC * r)))
        if (dist[i] < TIP_FACTOR * r or angle > 180) and width > SHORT_TIP_MAX_WIDTH * r:
            continue
        fingers.append(Finger((int(p[0]), int(p[1])), round(angle, 1),
                              round(width / r, 2), round(float(dist[i]) / r, 2)))
    fingers.sort(key=lambda f: f.angle)
    return fingers


def is_cut(hand):
    # el antebrazo sale por abajo y da igual, pero si toca arriba o los
    # lados por encima de la palma es un dedo cortado
    x, y, w, h = hand.roi
    pts = hand.contour[:, 0, :]
    above = pts[pts[:, 1] < hand.palm_center[1]]
    m = 4
    border = (above[:, 0] - x < m) | (x + w - 1 - above[:, 0] < m) | (above[:, 1] - y < m)
    return bool(border.any())


def is_o_circle(hand):
    r2 = hand.palm_radius ** 2
    for hole in hand.holes:
        M = cv2.moments(hole)
        if M["m00"] == 0 or cv2.contourArea(hole) < O_HOLE_MIN_AREA * r2:
            continue
        a = _tip_angle(hand.palm_center, (M["m10"] / M["m00"], M["m01"] / M["m00"]))
        if O_HOLE_ANGLES[0] <= a <= O_HOLE_ANGLES[1]:
            return True
    return False


def top_extent(hand):
    # hasta donde llega la mano por encima de la palma
    # puño 1.22-1.51, mano abierta sin puntas detectadas 1.58+
    pts = hand.contour[:, 0, :].astype(np.float32)
    cx, cy = hand.palm_center
    ang = np.degrees(np.arctan2(cy - pts[:, 1], pts[:, 0] - cx))
    d = np.hypot(pts[:, 0] - cx, pts[:, 1] - cy)
    above = d[(ang >= TOP_ANGLES[0]) & (ang <= TOP_ANGLES[1])]
    if len(above) == 0:
        return 0.0
    return float(above.max() / hand.palm_radius)


def extract_features(hand):
    hull_area = cv2.contourArea(cv2.convexHull(hand.contour))
    _, _, w, h = hand.bbox
    return HandFeatures(fingers=find_fingers(hand), cut=is_cut(hand),
                        has_hole=hand.has_hole, o_hole=is_o_circle(hand),
                        solidity=hand.area / hull_area if hull_area else 0.0,
                        aspect_ratio=w / h if h else 0.0,
                        top_extent=round(top_extent(hand), 2))
