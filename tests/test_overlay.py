# overlay del paso 9 con una mano dibujada

import time

import cv2
import numpy as np

from lse_auth import config
from lse_auth.contours import find_hand_contour
from lse_auth.overlay import draw_overlay
from lse_auth.sequence_decoder import SequenceDecoder
from lse_auth.stabilizer import StableLetterDetector

W, H = 1280, 720


def synthetic_hand():
    # palma + un dedo dentro del recuadro
    x, y, w, h = config.roi_pixels(W, H)
    mask = np.zeros((H, W), np.uint8)
    cx, cy = x + w // 2, y + 2 * h // 3
    cv2.circle(mask, (cx, cy), 60, 255, -1)
    cv2.rectangle(mask, (cx - 15, cy - 180), (cx + 15, cy), 255, -1)
    return find_hand_contour(mask)


def frame():
    return np.full((H, W, 3), 128, np.uint8)


def test_every_state_draws_without_errors():
    hand = synthetic_hand()
    assert hand is not None
    detector = StableLetterDetector()
    decoder = SequenceDecoder(code="HOLA", verbose=False)
    blank = frame()
    # vacio, bloqueado
    view = draw_overlay(frame(), None, None, detector, decoder, now=0.0)
    assert view.shape == blank.shape and not np.array_equal(view, blank)
    # confirmando, mano cortada
    for i in range(5):
        detector.update("H", now=i / 30)
    draw_overlay(frame(), hand, "H", detector, decoder, cut=True, now=0.2)
    # confirmada, parte del codigo hecho
    for i in range(5, 30):
        detector.update("H", now=i / 30)
    decoder.feed("H", now=1.0)
    draw_overlay(frame(), hand, "H", detector, decoder, now=2.0)
    # mensaje de error y luego desbloqueado
    decoder.feed("L", now=3.0)
    draw_overlay(frame(), hand, "L", detector, decoder, now=3.5)
    for i, letter in enumerate("HOLA"):
        decoder.feed(letter, now=10.0 + i)
    draw_overlay(frame(), hand, "A", detector, decoder, now=20.0)


def test_mistake_message_disappears():
    decoder = SequenceDecoder(code="HOLA", verbose=False)
    detector = StableLetterDetector()
    decoder.feed("O", now=0.0)                       # mal
    with_message = draw_overlay(frame(), None, None, detector, decoder, now=1.0)
    without = draw_overlay(frame(), None, None, detector, decoder, now=10.0)
    bottom = slice(H - 70, H)
    assert not np.array_equal(with_message[bottom], without[bottom])


def test_overlay_is_cheap():
    hand = synthetic_hand()
    detector = StableLetterDetector()
    decoder = SequenceDecoder(code="HOLA", verbose=False)
    decoder.feed("H", now=0.0)
    views = [frame() for _ in range(50)]
    start = time.perf_counter()
    for view in views:
        draw_overlay(view, hand, "O", detector, decoder, now=1.0)
    per_frame_ms = (time.perf_counter() - start) / len(views) * 1000
    assert per_frame_ms < 5.0          # sale ~1.4 ms
