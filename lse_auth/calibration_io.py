import os

import numpy as np

from lse_auth import config


def save_calibration(intrinsics, dist_coeffs, image_size, rms, path=config.CALIBRATION_FILE):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    np.savez_compressed(path, intrinsics=intrinsics, dist_coeffs=dist_coeffs,
                        image_size=np.array(image_size, dtype=np.int32), rms=np.float64(rms))


def load_calibration(path=config.CALIBRATION_FILE):
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Calibration file not found: {path}\n"
                                "Run 'python calibration_main.py' first to create it.")
    data = np.load(path)
    w, h = data["image_size"]
    return data["intrinsics"], data["dist_coeffs"], (int(w), int(h)), float(data["rms"])


def scale_intrinsics(intrinsics, calib_size, new_size):
    # calibramos a 2560x1440 y capturamos a 1280x720 -> hay que escalar K
    # (los coef. de distorsion no cambian)
    sx = new_size[0] / calib_size[0]
    sy = new_size[1] / calib_size[1]
    if abs(sx - sy) > 0.01:
        print(f"[calibration] Warning: aspect ratio changed from {calib_size} "
              f"to {new_size}, the undistortion may not be accurate.")
    K = intrinsics.astype(np.float64).copy()
    K[0, :] *= sx
    K[1, :] *= sy
    return K
