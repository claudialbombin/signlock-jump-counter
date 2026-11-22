"""
Step 8 - Sequence decoder: remember up to 4 letters and lock / unlock.

The assignment asks for "a decoder that remembers up to 4 consecutive
patterns and grants or blocks access to the next block depending on
whether they are in the right order", with a way to forget the sequence.
Here the patterns are the letters confirmed by StableLetterDetector
(step 7), one per sign, and the right order is config.UNLOCK_SEQUENCE
(H-O-L-A).

Rules
-----
* A letter equal to the next expected one is appended to the buffer.
* A wrong letter empties the buffer: the user has to start again. If the
  wrong letter is the FIRST letter of the code (e.g. H after H-O), it is
  taken as a new start, so the user does not have to show it twice.
* When the buffer equals the whole code, the decoder is UNLOCKED and stays
  so (letters are ignored) until reset() is called.
* If a sequence is started but no correct letter arrives for
  SEQUENCE_TIMEOUT seconds, it is forgotten (the user got distracted).
  The timeout is checked in feed() and also in tick(), which the live loop
  calls every frame so it fires even when no letter is shown.

Every transition is printed (and kept in `events`) to debug and to make
the screenshots of the report.
"""

import time
from enum import Enum
from typing import List, Optional, Sequence, Tuple

from lse_auth import config


class Event(Enum):
    CORRECT = "correct"        # the letter was the expected one
    WRONG = "wrong"            # wrong letter: buffer emptied
    RESTART = "restart"        # wrong letter, but it starts the code again
    TIMEOUT = "timeout"        # too long without a correct letter
    UNLOCKED = "unlocked"      # the whole code has been shown
    RESET = "reset"            # reset() called from outside


class SequenceDecoder:
    """
    Remember the confirmed letters and decide whether to unlock.

    Usage in a live loop::

        decoder = SequenceDecoder()
        while not decoder.is_unlocked():
            letter = detector.update(classify(...))    # step 7
            if letter is not None:
                decoder.feed(letter)
            decoder.tick()
        # -> step 10: start the jump counter

    Parameters
    ----------
    code : sequence of str
        Letters to show in order (config.UNLOCK_SEQUENCE by default).
    timeout : float
        Seconds without a correct letter before the buffer is forgotten.
    verbose : bool
        Print every transition.
    """

    def __init__(self, code: Sequence[str] = config.UNLOCK_SEQUENCE,
                 timeout: float = config.SEQUENCE_TIMEOUT,
                 verbose: bool = True) -> None:
        if not code:
            raise ValueError("the unlock code needs at least one letter")
        self.code: Tuple[str, ...] = tuple(code)
        self.timeout = timeout
        self.verbose = verbose
        self.events: List[Tuple[float, Event, Optional[str]]] = []
        self.buffer: List[str] = []
        self._unlocked = False
        self._last_correct = 0.0

    # -- state used by the interface (step 9) ------------------------------

    def is_unlocked(self) -> bool:
        return self._unlocked

    @property
    def expected(self) -> Optional[str]:
        """Next letter to show, None once unlocked."""
        return None if self._unlocked else self.code[len(self.buffer)]

    @property
    def progress_text(self) -> str:
        """Buffer as the interface shows it, e.g. 'H-O-_-_'."""
        shown = list(self.buffer) + ["_"] * (len(self.code) - len(self.buffer))
        return "-".join(shown)

    @property
    def last_event(self) -> Optional[Tuple[float, Event, Optional[str]]]:
        """(time, event, letter) of the last transition, or None."""
        return self.events[-1] if self.events else None

    def time_left(self, now: Optional[float] = None) -> Optional[float]:
        """Seconds until the started sequence is forgotten (None if not started)."""
        if not self.buffer or self._unlocked:
            return None
        now = time.monotonic() if now is None else now
        return max(0.0, self.timeout - (now - self._last_correct))

    # -- transitions -------------------------------------------------------

    def _log(self, now: float, event: Event, letter: Optional[str]) -> None:
        self.events.append((now, event, letter))
        if self.verbose:
            shown = f" {letter}" if letter else ""
            print(f"[decoder] {event.value}{shown} -> {self.progress_text}"
                  f"{'  UNLOCKED' if self._unlocked else ''}")

    def reset(self, now: Optional[float] = None) -> None:
        """Forget the buffer and lock again."""
        now = time.monotonic() if now is None else now
        self.buffer, self._unlocked = [], False
        self._log(now, Event.RESET, None)

    def tick(self, now: Optional[float] = None) -> Optional[Event]:
        """Check the timeout. Call it once per frame. Returns TIMEOUT if it fired."""
        now = time.monotonic() if now is None else now
        if self.buffer and not self._unlocked and now - self._last_correct > self.timeout:
            self.buffer = []
            self._log(now, Event.TIMEOUT, None)
            return Event.TIMEOUT
        return None

    def feed(self, letter: str, now: Optional[float] = None) -> Optional[Event]:
        """
        Give the decoder one confirmed letter.

        Returns
        -------
        Event or None
            What happened (None when already unlocked: letters are ignored).
        """
        now = time.monotonic() if now is None else now
        if self._unlocked:
            return None
        self.tick(now)

        if letter == self.expected:
            self.buffer.append(letter)
            self._last_correct = now
            if len(self.buffer) == len(self.code):
                self._unlocked = True
                event = Event.UNLOCKED
            else:
                event = Event.CORRECT
        elif letter == self.code[0]:
            self.buffer = [letter]
            self._last_correct = now
            event = Event.RESTART
        else:
            self.buffer = []
            event = Event.WRONG
        self._log(now, event, letter)
        return event
