"""
jump_tracker
============

Proposed system of the project: a rope jump counter that tracks a black
shoe with a bounding box and counts jumps in real time. It only starts
after the security block (lse_auth) has unlocked the system.

Classical computer vision only (no deep learning):

    frame -> black shoe mask -> shoe blob -> tracker (bbox + centre)
    -> vertical position signal -> smoothing -> jump counter -> overlay

Each stage lives in its own module so it can be tested in isolation.
"""

__all__ = ["config"]