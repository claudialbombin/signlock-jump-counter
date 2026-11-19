"""
Global configuration for the LSE authentication block.

I keep every "magic number" and path here so that the rest of the modules
can import them instead of hard-coding values. If something has to be tuned
(camera index, resolution, folders...) this is the only file to touch.
"""

import os
import sys

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

# Root of the repository (the folder that contains this package).
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Camera parameters exported from the offline calibration (calibration_main.py).
CALIBRATION_DIR = os.path.join(PROJECT_ROOT, "calibration")
CALIBRATION_FILE = os.path.join(CALIBRATION_DIR, "camera_params.npz")

# Reference images of the LSE letters (downloaded, only for visual support).
REFERENCE_DIR = os.path.join(PROJECT_ROOT, "pasos", "referencia_lse")

# Our own captured images, one sub-folder per class (see step 2).
DATASET_DIR = os.path.join(PROJECT_ROOT, "pasos", "dataset_lse")

# ---------------------------------------------------------------------------
# Camera
# ---------------------------------------------------------------------------

CAMERA_INDEX = 0          # change to 1, 2... if the built-in webcam is not 0
FRAME_WIDTH = 1280        # requested capture size (the camera may ignore it)
FRAME_HEIGHT = 720

# Show the image like a mirror. It feels much more natural when you are
# looking at your own hand. Mirroring is always done AFTER undistorting,
# because the distortion model refers to the real (non-flipped) sensor.
MIRROR = True


def camera_backend() -> int:
    """
    Return the OpenCV capture backend that works best on each OS.

    On macOS AVFoundation is the native one, on Windows DirectShow avoids
    some annoying warnings, and on Linux we let OpenCV choose.
    """
    import cv2  # imported here so the config can be read without OpenCV

    if sys.platform == "darwin":
        return cv2.CAP_AVFOUNDATION
    if sys.platform.startswith("win"):
        return cv2.CAP_DSHOW
    return cv2.CAP_ANY
