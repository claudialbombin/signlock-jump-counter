# paso 8: recuerda hasta 4 letras y desbloquea si van en orden
# letra mala -> se vacia (si es la H se toma como nuevo comienzo)
# 30 s sin letra buena -> se olvida

import time
from enum import Enum

from lse_auth import config


class Event(Enum):
    CORRECT = "correct"
    WRONG = "wrong"
    RESTART = "restart"
    TIMEOUT = "timeout"
    UNLOCKED = "unlocked"
    RESET = "reset"


class SequenceDecoder:
    def __init__(self, code=config.UNLOCK_SEQUENCE, timeout=config.SEQUENCE_TIMEOUT, verbose=True):
        if len(code) == 0:
            raise ValueError("the unlock code needs at least one letter")
        self.code = tuple(code)
        self.timeout = timeout
        self.verbose = verbose
        self.events = []   # (t, evento, letra), se usa para los logs del paso 11
        self.buffer = []
        self._unlocked = False
        self._last_correct = 0.0

    def is_unlocked(self):
        return self._unlocked

    @property
    def expected(self):
        if self._unlocked:
            return None
        return self.code[len(self.buffer)]

    @property
    def progress_text(self):
        huecos = ["_"] * (len(self.code) - len(self.buffer))
        return "-".join(self.buffer + huecos)

    @property
    def last_event(self):
        if not self.events:
            return None
        return self.events[-1]

    def time_left(self, now=None):
        if not self.buffer or self._unlocked:
            return None
        if now is None:
            now = time.monotonic()
        return max(0.0, self.timeout - (now - self._last_correct))

    def _log(self, now, event, letter):
        self.events.append((now, event, letter))
        if self.verbose:
            s = f"[decoder] {event.value}"
            if letter:
                s += " " + letter
            s += " -> " + self.progress_text
            if self._unlocked:
                s += "  UNLOCKED"
            print(s)

    def reset(self, now=None):
        if now is None:
            now = time.monotonic()
        self.buffer = []
        self._unlocked = False
        self._log(now, Event.RESET, None)

    def tick(self, now=None):
        # se llama en cada frame para que el timeout salte aunque no hagas nada
        if now is None:
            now = time.monotonic()
        if self.buffer and not self._unlocked and now - self._last_correct > self.timeout:
            self.buffer = []
            self._log(now, Event.TIMEOUT, None)
            return Event.TIMEOUT
        return None

    def feed(self, letter, now=None):
        if now is None:
            now = time.monotonic()
        if self._unlocked:
            return None
        self.tick(now)

        if letter == self.expected:
            self.buffer.append(letter)
            self._last_correct = now
            if len(self.buffer) == len(self.code):
                self._unlocked = True
                ev = Event.UNLOCKED
            else:
                ev = Event.CORRECT
        elif letter == self.code[0]:
            self.buffer = [letter]
            self._last_correct = now
            ev = Event.RESTART
        else:
            self.buffer = []
            ev = Event.WRONG
        self._log(now, ev, letter)
        return ev
