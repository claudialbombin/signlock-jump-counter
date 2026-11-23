"""
Step 10 - The security block as one object, and the unlock loop.

Everything from step 3 to step 9 is wired here so the rest of the project
only sees two things:

* SecurityBlock: feed it one frame at a time with update(frame); it says
  whether the system is unlocked and draw(view) paints the interface.
* run_unlock(grabber, window): the blocking loop used by main.py. It shows
  the camera, learns the background, waits for the H-O-L-A code and
  returns True once it is unlocked (False if the user quits). Then main.py
  calls the jump counter (Tere's block).

The security block knows nothing about the tracker: it only answers
"unlocked or not", as step 10 of the plan asks.

Optionally every decoder event (correct letter, mistake, timeout, unlock)
is appended to a CSV, which is what step 11 needs to measure how reliable
the unlock is in real use.
"""

import csv
import os
import time
from typing import Optional, Sequence

import cv2
import numpy as np

from lse_auth import config
from lse_auth.classifier import classify
from lse_auth.contours import find_hand_contour
from lse_auth.features import extract_features
from lse_auth.overlay import draw_overlay
from lse_auth.segmentation import BackgroundModel, segment_hand
from lse_auth.sequence_decoder import SequenceDecoder
from lse_auth.stabilizer import State, StableLetterDetector

BACKGROUND_DELAY = 2.0      # seconds to take the hand out before the background is saved
UNLOCKED_HOLD = 1.5         # seconds DESBLOQUEADO stays on screen before the tracker starts
LOG_DIR = os.path.join(config.PROJECT_ROOT, "pasos", "lse", "pruebas")


class SecurityBlock:
    """
    Steps 3-9 for one frame at a time.

    Usage::

        security = SecurityBlock()
        while True:
            frame = grabber.read()
            unlocked = security.update(frame)
            cv2.imshow(window, security.draw(frame.copy()))
            if unlocked:
                break

    Parameters
    ----------
    code : sequence of str
        Unlock code (config.UNLOCK_SEQUENCE, H-O-L-A, by default).
    log_path : str, optional
        CSV where every decoder event is appended (step 11).
    """

    def __init__(self, code: Sequence[str] = config.UNLOCK_SEQUENCE,
                 log_path: Optional[str] = None) -> None:
        self.background = BackgroundModel()
        self.detector = StableLetterDetector()
        self.decoder = SequenceDecoder(code=code)
        self.log_path = log_path
        self._logged = 0                    # decoder events already written
        self._hand = None
        self._features = None
        self._letter: Optional[str] = None
        self.reset_background()

    # -- state ------------------------------------------------------------

    @property
    def unlocked(self) -> bool:
        return self.decoder.is_unlocked()

    @property
    def learning_background(self) -> bool:
        return not self.background.ready

    def reset_background(self, delay: float = BACKGROUND_DELAY) -> None:
        """Learn the empty scene again, after giving `delay` s to take the hand out."""
        self.background.reset()
        self.detector.reset()
        self._delay = delay
        self._background_from: Optional[float] = None    # set by the next update()
        self._hand = self._features = self._letter = None

    def lock(self) -> None:
        """Forget the code typed so far and lock again."""
        self.detector.reset()
        self.decoder.reset()
        self._log_events()

    # -- per frame ----------------------------------------------------------

    def update(self, frame: np.ndarray, now: Optional[float] = None) -> bool:
        """Process one frame (undistorted and mirrored). Returns True when unlocked."""
        now = time.monotonic() if now is None else now
        if self.unlocked:
            return True
        if self.learning_background:
            if self._background_from is None:
                self._background_from = now + self._delay
            if now >= self._background_from:
                self.background.add(frame)
            return False

        mask = segment_hand(frame, self.background.image)
        self._hand = find_hand_contour(mask)
        self._features = extract_features(self._hand) if self._hand else None
        self._letter = classify(self._features) if self._features else None
        confirmed = self.detector.update(self._letter, now)
        if confirmed is not None:
            self.decoder.feed(confirmed, now)
        self.decoder.tick(now)
        self._log_events()
        return self.unlocked

    def draw(self, view: np.ndarray, now: Optional[float] = None) -> np.ndarray:
        """Paint the interface on `view` (in place) and return it."""
        now = time.monotonic() if now is None else now
        if self.learning_background:
            x, y, w, h = config.roi_pixels(view.shape[1], view.shape[0])
            cv2.rectangle(view, (x, y), (x + w, y + h), (255, 255, 255), 2)
            start = self._background_from if self._background_from is not None else now + self._delay
            left = start - now
            text = (f"Saca la mano del recuadro ({left:.0f})" if left > 0
                    else "Guardando el fondo: no te muevas")
            cv2.putText(view, text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0,
                        (0, 0, 0), 6, cv2.LINE_AA)
            cv2.putText(view, text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0,
                        (0, 200, 255), 2, cv2.LINE_AA)
            return view
        # The letter on screen: the one being confirmed, or the confirmed one
        # while it is held (both are stable, unlike the raw per-frame letter)
        if self.detector.state is State.CONFIRMING:
            shown = self.detector.candidate
        elif self.detector.state in (State.CONFIRMED, State.WAITING_RESET):
            shown = self._letter if self._letter == self.detector.confirmed else None
        else:
            shown = None
        cut = bool(self._features and self._features.cut)
        return draw_overlay(view, self._hand, shown, self.detector, self.decoder,
                            cut=cut, now=now)

    # -- step 11 log --------------------------------------------------------

    def _log_events(self) -> None:
        """Append the new decoder events to the CSV log."""
        new = self.decoder.events[self._logged:]
        if not new or self.log_path is None:
            self._logged = len(self.decoder.events)
            return
        first = not os.path.exists(self.log_path)
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        with open(self.log_path, "a", newline="") as f:
            writer = csv.writer(f, lineterminator="\n")
            if first:
                writer.writerow(["wall_time", "t", "event", "letter", "progress"])
            for t, event, letter in new:
                writer.writerow([time.strftime("%Y-%m-%d %H:%M:%S"), f"{t:.2f}",
                                 event.value, letter or "", self.decoder.progress_text])
        self._logged = len(self.decoder.events)


def default_log_path() -> str:
    """pasos/lse/pruebas/sesion_YYYYmmdd_HHMMSS.csv"""
    return os.path.join(LOG_DIR, time.strftime("sesion_%Y%m%d_%H%M%S.csv"))


def draw_fps(view: np.ndarray, fps: float) -> None:
    """Frame rate in the top-right corner (the demo video must show it)."""
    text = f"{fps:4.1f} FPS"
    org = (view.shape[1] - 160, 40)
    cv2.putText(view, text, org, cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 5, cv2.LINE_AA)
    cv2.putText(view, text, org, cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2, cv2.LINE_AA)


def run_unlock(grabber, window: str,
               code: Sequence[str] = config.UNLOCK_SEQUENCE,
               log_path: Optional[str] = None) -> bool:
    """
    Blocking unlock loop: show the camera until the code is spelled.

    Parameters
    ----------
    grabber : lse_auth.camera.FrameGrabber
        Source of undistorted, mirrored frames (shared with the tracker).
    window : str
        OpenCV window to draw in (shared with the tracker).
    code : sequence of str
        Unlock code.
    log_path : str, optional
        CSV for the step 11 measurements.

    Returns
    -------
    bool
        True when unlocked, False if the user quit (q / ESC) or the camera
        stopped.

    Keys: f = learn the background again, r = lock and start the code
    again, q / ESC = quit.
    """
    security = SecurityBlock(code=code, log_path=log_path)
    fps, last = 0.0, time.perf_counter()
    unlocked_at: Optional[float] = None
    while True:
        frame = grabber.read()
        if frame is None:
            return False
        if security.update(frame) and unlocked_at is None:
            unlocked_at = time.monotonic()
        view = security.draw(frame.copy())

        now = time.perf_counter()
        fps = 0.9 * fps + 0.1 / max(now - last, 1e-6)
        last = now
        draw_fps(view, fps)
        cv2.imshow(window, view)

        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), 27):
            return False
        if key == ord("f"):
            security.reset_background()
        elif key == ord("r"):
            security.lock()
            unlocked_at = None
        if unlocked_at is not None and time.monotonic() - unlocked_at >= UNLOCKED_HOLD:
            return True
