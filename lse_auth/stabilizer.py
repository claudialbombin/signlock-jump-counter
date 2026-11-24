# paso 7: el clasificador parpadea de un frame a otro, esto hace que cada
# signo cuente una sola vez
# WAITING -> CONFIRMING -> CONFIRMED -> WAITING_RESET -> WAITING

import time
from collections import Counter, deque
from enum import Enum

from lse_auth import config


class State(Enum):
    WAITING = "waiting"
    CONFIRMING = "confirming"
    CONFIRMED = "confirmed"
    WAITING_RESET = "waiting_reset"


class StableLetterDetector:
    def __init__(self, confirm_time=config.STABLE_CONFIRM_TIME,
                 min_share=config.STABLE_MIN_SHARE,
                 min_frames=config.STABLE_MIN_FRAMES,
                 reset_time=config.STABLE_RESET_TIME):
        self.confirm_time = confirm_time
        self.min_share = min_share
        self.min_frames = min_frames
        self.reset_time = reset_time
        self.reset()

    def reset(self):
        self.state = State.WAITING
        self.candidate = None
        self.confirmed = None
        self._history = deque()
        self._candidate_since = 0.0
        self._gone_since = None
        self._now = 0.0

    @property
    def progress(self):
        # para la barrita de la pantalla
        if self.state == State.CONFIRMED:
            return 1.0
        if self.state != State.CONFIRMING:
            return 0.0
        return min(1.0, (self._now - self._candidate_since) / self.confirm_time)

    def _most_frequent(self):
        letters = [l for _, l in self._history]
        c = Counter(l for l in letters if l is not None)
        if not c:
            return None, 0.0, len(letters)
        best, n = c.most_common(1)[0]
        return best, n / len(letters), len(letters)

    def update(self, letter, now=None):
        if now is None:
            now = time.monotonic()
        self._now = now
        self._history.append((now, letter))
        while self._history and now - self._history[0][0] > self.confirm_time:
            self._history.popleft()

        if self.state == State.CONFIRMED or self.state == State.WAITING_RESET:
            # ya confirmada: hasta que no desaparezca un rato no se vuelve a contar
            self.state = State.WAITING_RESET
            if letter == self.confirmed:
                self._gone_since = None
                return None
            if self._gone_since is None:
                self._gone_since = now
            if now - self._gone_since < self.reset_time:
                return None
            self.state = State.WAITING
            self._gone_since = None
            # quitar los frames de la letra vieja
            self._history = deque(x for x in self._history if x[1] != self.confirmed)

        best, share, frames = self._most_frequent()
        if best is None:
            self.state = State.WAITING
            self.candidate = None
            return None
        if best != self.candidate or self.state == State.WAITING:
            self.state = State.CONFIRMING
            self.candidate = best
            self._candidate_since = now
        if now - self._candidate_since >= self.confirm_time and share >= self.min_share \
                and frames >= self.min_frames:
            self.state = State.CONFIRMED
            self.confirmed = best
            self.candidate = None
            return best
        return None
