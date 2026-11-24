"""
Tests of the step 10 SecurityBlock with real dataset frames (no camera).

Run with:  python -m pytest tests/test_security.py
"""

import csv
import os

import cv2
import pytest

from lse_auth import SecurityBlock, config

DATASET = config.DATASET_DIR
BACKGROUND = os.path.join(DATASET, "_background", "bg_06.jpg")
FIST = os.path.join(DATASET, "A", "img_53.jpg")
OPEN_HAND = os.path.join(DATASET, "NONE", "img_70.jpg")

pytestmark = pytest.mark.skipif(not os.path.exists(FIST), reason="dataset not available")
FPS = 30.0


def learn_background(security, background):
    t = 10.0
    while security.learning_background:
        security.update(background, now=t)
        t += 1 / FPS
    return t


def show(security, frame, seconds, t):
    for _ in range(int(seconds * FPS)):
        security.update(frame, now=t)
        t += 1 / FPS
    return t


def test_unlocks_with_the_right_letter_and_logs_it(tmp_path):
    log = str(tmp_path / "log.csv")
    security = SecurityBlock(code="A", log_path=log)
    background, fist = cv2.imread(BACKGROUND), cv2.imread(FIST)
    t = learn_background(security, background)
    assert not security.unlocked
    show(security, fist, 1.0, t)
    assert security.unlocked
    rows = list(csv.DictReader(open(log)))
    assert [r["event"] for r in rows] == ["unlocked"] and rows[0]["letter"] == "A"


def test_other_gestures_do_not_unlock():
    security = SecurityBlock(code="A")
    background = cv2.imread(BACKGROUND)
    t = learn_background(security, background)
    t = show(security, cv2.imread(OPEN_HAND), 2.0, t)
    t = show(security, background, 1.0, t)
    assert not security.unlocked


def test_draw_in_every_phase():
    security = SecurityBlock(code="A")
    background, fist = cv2.imread(BACKGROUND), cv2.imread(FIST)
    security.draw(background.copy(), now=0.0)            # countdown
    t = learn_background(security, background)
    security.draw(fist.copy(), now=t)                    # locked
    show(security, fist, 1.0, t)
    view = security.draw(fist.copy(), now=t + 1.0)       # unlocked
    assert view.shape == fist.shape


def test_lock_starts_again():
    security = SecurityBlock(code="A")
    background, fist = cv2.imread(BACKGROUND), cv2.imread(FIST)
    t = show(security, fist, 1.0, learn_background(security, background))
    assert security.unlocked
    security.lock()
    assert not security.unlocked and security.decoder.buffer == []
