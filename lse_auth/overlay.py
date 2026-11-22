"""
Step 9 - On-screen feedback for the user.

draw_overlay() draws, on top of the camera frame, everything the person
needs to see while spelling the code (and what the demo video shows):

* top-left corner: a big BLOQUEADO (red) / DESBLOQUEADO (green) badge;
* under it, one box per letter of the code. The letters already shown are
  written in green, the box of the next one is highlighted in yellow and
  the rest are empty. The pending letters are NOT written: the code is a
  password, the screen must not give it away. Under the boxes, the seconds
  left before a started sequence is forgotten;
* the hand box (ROI) and the hand contour + bounding box: orange while the
  letter is being recognised, green once it is confirmed;
* next to the box, the letter of the current frame, small and grey (it is
  not confirmed yet), with a bar that fills while step 7 confirms it;
* for 2.5 s after a mistake, a red message ("Secuencia incorrecta,
  intentalo de nuevo" / "Tiempo agotado, empieza de nuevo");
* "Mete toda la mano en el recuadro" when the hand is cut by the box.

cv2.putText only has ASCII fonts, so the texts have no accents.

It only draws a few rectangles, one contour and some text (~1 ms at
1280x720, see pasos/lse/09_feedback_visual.md): it does not lower the frame
rate. Everything is drawn in place on the given frame, which is returned
too, so it can be chained.
"""

import time
from typing import Optional, Tuple

import cv2
import numpy as np

from lse_auth import config
from lse_auth.contours import HandContour
from lse_auth.sequence_decoder import Event, SequenceDecoder
from lse_auth.stabilizer import State, StableLetterDetector

MESSAGE_TIME = 2.5          # seconds a mistake message stays on screen

# BGR colours
RED = (0, 0, 230)
GREEN = (0, 200, 0)
ORANGE = (0, 165, 255)
YELLOW = (0, 230, 255)
GREY = (170, 170, 170)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

FONT = cv2.FONT_HERSHEY_SIMPLEX
MESSAGES = {
    Event.WRONG: "Secuencia incorrecta, intentalo de nuevo",
    Event.TIMEOUT: "Tiempo agotado, empieza de nuevo",
}


def _text(view: np.ndarray, text: str, org: Tuple[int, int], scale: float,
          color: Tuple[int, int, int], thickness: int = 2) -> None:
    """Text with a black outline, readable over any background."""
    cv2.putText(view, text, org, FONT, scale, BLACK, thickness + 4, cv2.LINE_AA)
    cv2.putText(view, text, org, FONT, scale, color, thickness, cv2.LINE_AA)


def _draw_status(view: np.ndarray, unlocked: bool) -> None:
    """BLOQUEADO / DESBLOQUEADO badge in the top-left corner."""
    text, color = ("DESBLOQUEADO", GREEN) if unlocked else ("BLOQUEADO", RED)
    (tw, th), _ = cv2.getTextSize(text, FONT, 1.3, 3)
    cv2.rectangle(view, (20, 20), (20 + tw + 30, 20 + th + 30), color, -1)
    cv2.putText(view, text, (35, 35 + th), FONT, 1.3, WHITE, 3, cv2.LINE_AA)


def _draw_code(view: np.ndarray, decoder: SequenceDecoder, now: float) -> None:
    """One box per letter of the code, with the letters already shown."""
    size, gap, x0, y0 = 64, 12, 20, 100
    done = len(decoder.buffer)
    for i in range(len(decoder.code)):
        x = x0 + i * (size + gap)
        if i < done:
            color, thickness = GREEN, 3
        elif i == done and not decoder.is_unlocked():
            color, thickness = YELLOW, 3
        else:
            color, thickness = GREY, 2
        cv2.rectangle(view, (x, y0), (x + size, y0 + size), BLACK, thickness + 3)
        cv2.rectangle(view, (x, y0), (x + size, y0 + size), color, thickness)
        if i < done:
            (tw, th), _ = cv2.getTextSize(decoder.buffer[i], FONT, 1.6, 4)
            _text(view, decoder.buffer[i],
                  (x + (size - tw) // 2, y0 + (size + th) // 2), 1.6, GREEN, 4)
    left = decoder.time_left(now)
    if left is not None:
        _text(view, f"{left:.0f} s", (x0, y0 + size + 32), 0.8, WHITE)


def _draw_message(view: np.ndarray, decoder: SequenceDecoder, now: float) -> None:
    """Red message for MESSAGE_TIME seconds after a mistake or a timeout."""
    last = decoder.last_event
    if last is None or now - last[0] > MESSAGE_TIME or last[1] not in MESSAGES:
        return
    text = MESSAGES[last[1]]
    (tw, _), _ = cv2.getTextSize(text, FONT, 1.0, 2)
    _text(view, text, ((view.shape[1] - tw) // 2, view.shape[0] - 30), 1.0, RED)


def _draw_hand(view: np.ndarray, hand: Optional[HandContour],
               roi: Tuple[int, int, int, int], letter: Optional[str],
               detector: StableLetterDetector, cut: bool) -> None:
    """Contour, bounding box, current letter and confirmation bar."""
    x, y, w, _ = roi
    confirmed = (detector.state in (State.CONFIRMED, State.WAITING_RESET)
                 and letter is not None and letter == detector.confirmed)
    color = GREEN if confirmed else ORANGE
    if hand is not None:
        cv2.drawContours(view, [hand.contour], -1, color, 2, cv2.LINE_8)
        bx, by, bw, bh = hand.bbox
        cv2.rectangle(view, (bx, by), (bx + bw, by + bh), color, 1)

    # Letter of this frame: small and grey until it is confirmed
    tx, ty = x + w + 15, y + 60
    if letter is not None:
        _text(view, letter, (tx, ty), 2.0, GREEN if confirmed else GREY, 4)
    bar_w, bar_y = 100, ty + 20
    if detector.state is State.CONFIRMING:
        cv2.rectangle(view, (tx, bar_y), (tx + bar_w, bar_y + 12), WHITE, 1)
        cv2.rectangle(view, (tx, bar_y),
                      (tx + int(bar_w * detector.progress), bar_y + 12), GREEN, -1)
    if cut:
        _text(view, "Mete toda la mano en el recuadro", (x, y - 12), 0.7, RED)


def draw_overlay(view: np.ndarray, hand: Optional[HandContour], letter: Optional[str],
                 detector: StableLetterDetector, decoder: SequenceDecoder,
                 cut: bool = False, now: Optional[float] = None) -> np.ndarray:
    """
    Draw the user feedback on the frame (in place) and return it.

    Parameters
    ----------
    view : np.ndarray
        BGR frame to draw on (usually a copy of the camera frame).
    hand : HandContour or None
        Step 4 output for this frame (None when the box is empty).
    letter : str or None
        Letter of this frame (step 6, optionally smoothed): shown small and
        grey until the stabiliser confirms it.
    detector : StableLetterDetector
        Step 7, for the confirmation bar and the contour colour.
    decoder : SequenceDecoder
        Step 8, for the code progress, the lock state and the messages.
    cut : bool
        features.cut: the hand leaves the box.
    now : float, optional
        time.monotonic() by default (the decoder uses the same clock).
    """
    now = time.monotonic() if now is None else now
    roi = config.roi_pixels(view.shape[1], view.shape[0])
    x, y, w, h = roi
    cv2.rectangle(view, (x, y), (x + w, y + h),
                  GREEN if decoder.is_unlocked() else WHITE, 2)
    _draw_hand(view, hand, roi, letter, detector, cut)
    _draw_status(view, decoder.is_unlocked())
    _draw_code(view, decoder, now)
    _draw_message(view, decoder, now)
    return view
