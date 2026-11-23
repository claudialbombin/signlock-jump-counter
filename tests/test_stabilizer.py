"""
Tests of the step 7 StableLetterDetector with synthetic letter streams.

Run with:  python -m pytest tests/test_stabilizer.py
"""

import random

from lse_auth.stabilizer import State, StableLetterDetector

FPS = 30.0


def run(letters, fps=FPS, detector=None):
    """Feed a list of per-frame letters at a fixed rate; return the confirmed ones."""
    detector = detector or StableLetterDetector()
    out = []
    for i, letter in enumerate(letters):
        confirmed = detector.update(letter, now=i / fps)
        if confirmed is not None:
            out.append(confirmed)
    return out


def frames(letter, seconds, fps=FPS):
    return [letter] * int(round(seconds * fps))


def test_held_letter_is_confirmed_once():
    assert run(frames("H", 10)) == ["H"]


def test_short_letter_is_not_confirmed():
    assert run(frames(None, 1) + frames("H", 0.3) + frames(None, 1)) == []


def test_hola_with_hand_out_between_letters():
    stream = []
    for letter in "HOL":
        stream += frames(letter, 1.5) + frames(None, 0.5)
    assert run(stream) == ["H", "O", "L"]


def test_direct_change_without_taking_the_hand_out():
    assert run(frames("H", 1) + frames("O", 1) + frames("L", 1)) == ["H", "O", "L"]


def test_same_letter_twice_needs_a_gap():
    assert run(frames("O", 1) + frames("O", 1)) == ["O"]
    assert run(frames("O", 1) + frames(None, 0.5) + frames("O", 1)) == ["O", "O"]


def test_single_wrong_frames_do_not_break_the_letter():
    random.seed(0)
    stream = [("L" if random.random() < 0.9 else random.choice(["H", None]))
              for _ in range(int(2 * FPS))]
    assert run(stream) == ["L"]


def test_flicker_between_two_letters_is_not_confirmed():
    assert run(["H", "L"] * int(FPS)) == []


def test_short_dropout_while_holding_does_not_repeat_the_letter():
    # 2 frames lost (< STABLE_RESET_TIME) in the middle of a held H
    assert run(frames("H", 1) + frames(None, 2 / FPS) + frames("H", 1)) == ["H"]


def test_works_at_low_frame_rate():
    assert run(frames("O", 2, fps=15), fps=15) == ["O"]


def test_states_and_progress():
    detector = StableLetterDetector()
    detector.update(None, now=0.0)
    assert detector.state is State.WAITING and detector.progress == 0.0
    detector.update("H", now=0.1)
    detector.update("H", now=0.3)
    assert detector.state is State.CONFIRMING and 0.0 < detector.progress < 1.0
    t = 0.3
    while detector.update("H", now=t) is None:
        t += 1 / FPS
    assert detector.state is State.CONFIRMED and detector.confirmed == "H"
    detector.update("H", now=t + 0.1)
    assert detector.state is State.WAITING_RESET
    detector.reset()
    assert detector.state is State.WAITING and detector.confirmed is None
