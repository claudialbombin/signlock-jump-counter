# paso 10: todo junto. main.py solo usa run_unlock
# este bloque no sabe nada del tracker, solo dice si esta desbloqueado

import csv
import os
import time

import cv2

from lse_auth import config
from lse_auth.classifier import classify
from lse_auth.contours import find_hand_contour
from lse_auth.features import extract_features
from lse_auth.overlay import draw_overlay
from lse_auth.segmentation import BackgroundModel, segment_hand
from lse_auth.sequence_decoder import SequenceDecoder
from lse_auth.stabilizer import State, StableLetterDetector

BACKGROUND_DELAY = 2.0   # tiempo para sacar la mano antes de guardar el fondo
UNLOCKED_HOLD = 1.5
LOG_DIR = os.path.join(config.PROJECT_ROOT, "pasos", "lse", "pruebas")


class SecurityBlock:
    def __init__(self, code=config.UNLOCK_SEQUENCE, log_path=None):
        self.background = BackgroundModel()
        self.detector = StableLetterDetector()
        self.decoder = SequenceDecoder(code=code)
        self.log_path = log_path   # csv para el paso 11
        self._logged = 0
        self._hand = None
        self._features = None
        self._letter = None
        self.reset_background()

    @property
    def unlocked(self):
        return self.decoder.is_unlocked()

    @property
    def learning_background(self):
        return not self.background.ready

    def reset_background(self, delay=BACKGROUND_DELAY):
        self.background.reset()
        self.detector.reset()
        self._delay = delay
        self._background_from = None
        self._hand = None
        self._features = None
        self._letter = None

    def lock(self):
        self.detector.reset()
        self.decoder.reset()
        self._log_events()

    def update(self, frame, now=None):
        if now is None:
            now = time.monotonic()
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
        self._features = None
        self._letter = None
        if self._hand is not None:
            self._features = extract_features(self._hand)
            self._letter = classify(self._features)

        l = self.detector.update(self._letter, now)
        if l is not None:
            self.decoder.feed(l, now)
        self.decoder.tick(now)
        self._log_events()
        return self.unlocked

    def draw(self, view, now=None):
        if now is None:
            now = time.monotonic()

        if self.learning_background:
            x, y, w, h = config.roi_pixels(view.shape[1], view.shape[0])
            cv2.rectangle(view, (x, y), (x + w, y + h), (255, 255, 255), 2)
            start = self._background_from
            if start is None:
                start = now + self._delay
            left = start - now
            if left > 0:
                msg = f"Saca la mano del recuadro ({left:.0f})"
            else:
                msg = "Guardando el fondo: no te muevas"
            cv2.putText(view, msg, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 6, cv2.LINE_AA)
            cv2.putText(view, msg, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 200, 255), 2, cv2.LINE_AA)
            return view

        # la letra del frame parpadea, enseño la candidata o la confirmada
        shown = None
        if self.detector.state == State.CONFIRMING:
            shown = self.detector.candidate
        elif self.detector.state in (State.CONFIRMED, State.WAITING_RESET):
            if self._letter == self.detector.confirmed:
                shown = self._letter
        cut = self._features is not None and self._features.cut
        return draw_overlay(view, self._hand, shown, self.detector, self.decoder, cut=cut, now=now)

    def _log_events(self):
        nuevos = self.decoder.events[self._logged:]
        self._logged = len(self.decoder.events)
        if not nuevos or self.log_path is None:
            return
        first = not os.path.exists(self.log_path)
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        with open(self.log_path, "a", newline="") as f:
            w = csv.writer(f, lineterminator="\n")
            if first:
                w.writerow(["wall_time", "t", "event", "letter", "progress"])
            for t, ev, letter in nuevos:
                w.writerow([time.strftime("%Y-%m-%d %H:%M:%S"), f"{t:.2f}", ev.value,
                            letter or "", self.decoder.progress_text])


def default_log_path(tag=None):
    name = time.strftime("sesion_%Y%m%d_%H%M%S")
    if tag:
        clean = ""
        for c in tag.lower():
            clean += c if (c.isalnum() or c == "-") else "-"
        name += "_" + clean
    return os.path.join(LOG_DIR, name + ".csv")


def draw_fps(view, fps):
    pos = (view.shape[1] - 160, 40)
    cv2.putText(view, f"{fps:4.1f} FPS", pos, cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 5, cv2.LINE_AA)
    cv2.putText(view, f"{fps:4.1f} FPS", pos, cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2, cv2.LINE_AA)


def run_unlock(grabber, window, code=config.UNLOCK_SEQUENCE, log_path=None):
    # True si se desbloquea, False si sales (q / ESC)
    # f = fondo otra vez, r = bloquear y empezar de nuevo
    security = SecurityBlock(code=code, log_path=log_path)
    fps = 0.0
    last = time.perf_counter()
    unlocked_at = None
    while True:
        frame = grabber.read()
        if frame is None:
            return False
        if security.update(frame) and unlocked_at is None:
            unlocked_at = time.monotonic()
        view = security.draw(frame.copy())

        t = time.perf_counter()
        fps = 0.9 * fps + 0.1 / max(t - last, 1e-6)
        last = t
        draw_fps(view, fps)
        cv2.imshow(window, view)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q") or key == 27:
            return False
        if key == ord("f"):
            security.reset_background()
        elif key == ord("r"):
            security.lock()
            unlocked_at = None

        # dejar DESBLOQUEADO un momento en pantalla antes de pasar al tracker
        if unlocked_at is not None and time.monotonic() - unlocked_at >= UNLOCKED_HOLD:
            return True
