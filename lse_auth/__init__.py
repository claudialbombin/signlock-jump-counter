"""
lse_auth
========

Security block of the project: the user unlocks the system by fingerspelling
the word H-O-L-A with the Spanish Sign Language (LSE) manual alphabet.

The whole pipeline uses classical computer vision only (no deep learning),
as required by the project guidelines:

    camera frame -> undistort (calibration) -> skin segmentation
    -> hand contour -> shape features -> rule-based classifier
    -> temporal stabilisation -> sequence decoder (unlock / lock)

Each stage lives in its own module so it can be tested in isolation.

Public interface (step 10)
--------------------------
The rest of the project only needs::

    from lse_auth import run_unlock
    if run_unlock(grabber, window):      # blocks until H-O-L-A is spelled
        run_tracker(grabber, window)     # next block

or, inside another loop, SecurityBlock.update(frame) -> bool. See main.py
and lse_auth/security.py.
"""

from lse_auth.security import SecurityBlock, run_unlock

__all__ = ["config", "SecurityBlock", "run_unlock"]
