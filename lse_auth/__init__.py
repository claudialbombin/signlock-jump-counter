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
"""

__all__ = ["config"]
