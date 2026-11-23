"""
Step 7 - Temporal stabilisation of the letter.

The classifier of step 6 answers frame by frame and flickers: a frame with
a bad mask, a finger crossing the box or the hand moving between two
letters gives a wrong letter or None for a frame or two. The sequence
decoder (step 8) must not see that noise, and it must receive every letter
the user shows ONCE, not once per frame.

StableLetterDetector is a small state machine:

    WAITING        no letter in the recent frames
       |  a letter becomes the most frequent one
       v
    CONFIRMING     the same letter is the most frequent one for
       |           STABLE_CONFIRM_TIME seconds and fills STABLE_MIN_SHARE
       |           of the frames (another letter in between restarts it)
       v
    CONFIRMED      update() returns the letter, only in this frame
       |
       v
    WAITING_RESET  the confirmed letter is still shown: nothing is emitted.
       |           Once it has been gone (no hand, no letter or another
       |           letter) for STABLE_RESET_TIME, back to WAITING.
       v
    WAITING

Holding the H for ten seconds therefore gives one H. Going straight from H
to O without taking the hand out also works: the O makes the H disappear,
so the detector is re-armed and the O is then confirmed as usual. Showing
the same letter twice in a row needs the hand out (or any other gesture) in
between, which is also what a person would do.

Times are measured in seconds, not frames, so the behaviour does not
depend on the speed of the laptop.
"""

import time
from collections import Counter, deque
from enum import Enum
from typing import Deque, Optional, Tuple

from lse_auth import config


class State(Enum):
    WAITING = "waiting"
    CONFIRMING = "confirming"
    CONFIRMED = "confirmed"
    WAITING_RESET = "waiting_reset"


class StableLetterDetector:
    """
    Turn the noisy per-frame letters into single, confirmed letters.

    Usage in a live loop::

        detector = StableLetterDetector()
        while True:
            letter = classify(...)            # "H", "O", "L" or None
            confirmed = detector.update(letter)
            if confirmed is not None:
                decoder.feed(confirmed)        # step 8

    Parameters
    ----------
    confirm_time, min_share, min_frames, reset_time
        See config.STABLE_* (the defaults).
    """

    def __init__(self, confirm_time: float = config.STABLE_CONFIRM_TIME,
                 min_share: float = config.STABLE_MIN_SHARE,
                 min_frames: int = config.STABLE_MIN_FRAMES,
                 reset_time: float = config.STABLE_RESET_TIME) -> None:
        self.confirm_time = confirm_time
        self.min_share = min_share
        self.min_frames = min_frames
        self.reset_time = reset_time
        self.reset()

    def reset(self) -> None:
        """Forget everything (e.g. after recapturing the background)."""
        self.state = State.WAITING
        self.candidate: Optional[str] = None      # letter being confirmed
        self.confirmed: Optional[str] = None      # last confirmed letter
        self._history: Deque[Tuple[float, Optional[str]]] = deque()
        self._candidate_since = 0.0
        self._gone_since: Optional[float] = None
        self._now = 0.0

    @property
    def progress(self) -> float:
        """0..1, how far the candidate is from being confirmed (for the UI)."""
        if self.state is not State.CONFIRMING:
            return 1.0 if self.state is State.CONFIRMED else 0.0
        return min(1.0, (self._now - self._candidate_since) / self.confirm_time)

    def _most_frequent(self) -> Tuple[Optional[str], float, int]:
        """Most frequent letter of the window, its share and the window size."""
        letters = [letter for _, letter in self._history]
        counts = Counter(letter for letter in letters if letter is not None)
        if not counts:
            return None, 0.0, len(letters)
        letter, count = counts.most_common(1)[0]
        return letter, count / len(letters), len(letters)

    def update(self, letter: Optional[str], now: Optional[float] = None) -> Optional[str]:
        """
        Feed the letter of one frame.

        Parameters
        ----------
        letter : str or None
            Output of classifier.classify for this frame.
        now : float, optional
            Time of the frame in seconds (time.monotonic() by default; the
            tests pass it explicitly).

        Returns
        -------
        str or None
            The letter, only in the frame where it gets confirmed.
        """
        now = time.monotonic() if now is None else now
        self._now = now
        self._history.append((now, letter))
        while self._history and now - self._history[0][0] > self.confirm_time:
            self._history.popleft()

        if self.state in (State.CONFIRMED, State.WAITING_RESET):
            self.state = State.WAITING_RESET
            if letter == self.confirmed:
                self._gone_since = None
                return None
            if self._gone_since is None:
                self._gone_since = now
            if now - self._gone_since < self.reset_time:
                return None
            # Re-armed. Frames of the old letter must not count any more.
            self.state, self._gone_since = State.WAITING, None
            self._history = deque(item for item in self._history
                                  if item[1] != self.confirmed)

        best, share, frames = self._most_frequent()
        if best is None:
            self.state, self.candidate = State.WAITING, None
            return None
        if best != self.candidate or self.state is State.WAITING:
            self.state, self.candidate = State.CONFIRMING, best
            self._candidate_since = now
        if (now - self._candidate_since >= self.confirm_time
                and share >= self.min_share and frames >= self.min_frames):
            self.state, self.confirmed, self.candidate = State.CONFIRMED, best, None
            return best
        return None
