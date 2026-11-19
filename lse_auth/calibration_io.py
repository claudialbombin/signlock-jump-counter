"""
Save and load the camera parameters obtained in the offline calibration.

The calibration (calibration_main.py) is slow-ish and must be done offline,
so instead of recomputing it every time we run the system, its result is
stored once in a .npz file and loaded at start-up.

The calibration images were taken at 2560x1440, but the live system usually
captures at a smaller size (1280x720). The intrinsic matrix depends on the
resolution, so it has to be rescaled before undistorting. The distortion
coefficients do NOT change with resolution because they are defined on
normalised image coordinates.
"""

import os
from typing import Tuple

import numpy as np

from lse_auth import config


def save_calibration(intrinsics: np.ndarray, dist_coeffs: np.ndarray,
                     image_size: Tuple[int, int], rms: float,
                     path: str = config.CALIBRATION_FILE) -> None:
    """
    Store the calibration result in a compressed .npz file.

    Parameters
    ----------
    intrinsics : np.ndarray
        3x3 camera matrix K.
    dist_coeffs : np.ndarray
        Distortion coefficients (k1, k2, p1, p2, k3).
    image_size : tuple of int
        (width, height) of the images used to calibrate.
    rms : float
        Root mean squared reprojection error, kept for the report.
    path : str
        Output file.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    np.savez_compressed(path,
                        intrinsics=intrinsics,
                        dist_coeffs=dist_coeffs,
                        image_size=np.array(image_size, dtype=np.int32),
                        rms=np.float64(rms))


def load_calibration(path: str = config.CALIBRATION_FILE
                     ) -> Tuple[np.ndarray, np.ndarray, Tuple[int, int], float]:
    """
    Load the parameters saved by save_calibration().

    Returns
    -------
    intrinsics : np.ndarray
        3x3 camera matrix K at the calibration resolution.
    dist_coeffs : np.ndarray
        Distortion coefficients.
    image_size : tuple of int
        (width, height) used during the calibration.
    rms : float
        Reprojection error of the calibration.
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"Calibration file not found: {path}\n"
            "Run 'python calibration_main.py' first to create it.")
    data = np.load(path)
    width, height = (int(v) for v in data["image_size"])
    return data["intrinsics"], data["dist_coeffs"], (width, height), float(data["rms"])


def scale_intrinsics(intrinsics: np.ndarray, calib_size: Tuple[int, int],
                     new_size: Tuple[int, int]) -> np.ndarray:
    """
    Adapt the camera matrix to a different image resolution.

    If the image is resized by a factor s, the focal lengths (fx, fy) and the
    principal point (cx, cy) are multiplied by s too:

        K' = [[s_x * fx,    0,     s_x * cx],
              [   0,     s_y * fy, s_y * cy],
              [   0,        0,        1    ]]

    This is only valid if the camera keeps the same field of view, i.e. the
    new resolution has the same aspect ratio (16:9 -> 16:9). If not, the
    camera is probably cropping the sensor and we warn about it.

    Parameters
    ----------
    intrinsics : np.ndarray
        3x3 camera matrix at calib_size.
    calib_size, new_size : tuple of int
        (width, height) before and after.

    Returns
    -------
    np.ndarray
        3x3 camera matrix valid for new_size.
    """
    sx = new_size[0] / calib_size[0]
    sy = new_size[1] / calib_size[1]
    if abs(sx - sy) > 0.01:
        print(f"[calibration] Warning: aspect ratio changed from {calib_size} "
              f"to {new_size}, the undistortion may not be accurate.")

    scaled = intrinsics.astype(np.float64).copy()
    scaled[0, :] *= sx     # fx, skew, cx
    scaled[1, :] *= sy     # fy, cy
    return scaled
