"""
Camera input with lens distortion correction.

Every frame that enters the LSE pipeline must be undistorted with the
parameters of the offline calibration (step 2 and step 3 of the plan).

cv2.undistort() recomputes the correction maps on every call, which is slow
for real time. Since the camera and the resolution never change while the
program runs, we compute the maps ONCE with cv2.initUndistortRectifyMap()
and then each frame only needs a cv2.remap(), which is much cheaper.
"""

import threading
from typing import Optional, Tuple

import cv2
import numpy as np

from lse_auth import config
from lse_auth.calibration_io import load_calibration, scale_intrinsics


class Undistorter:
    """
    Removes the lens distortion from frames of a fixed size.

    Parameters
    ----------
    frame_size : tuple of int
        (width, height) of the frames that will be corrected.
    calibration_file : str
        Path to the .npz created by calibration_main.py.
    alpha : float
        Free scaling parameter of cv2.getOptimalNewCameraMatrix():
        0 -> crop so that there are no black borders,
        1 -> keep every original pixel (black curved borders appear).
        I use 0 because black borders could be confused with background
        later in the segmentation.
    """

    def __init__(self, frame_size: Tuple[int, int],
                 calibration_file: str = config.CALIBRATION_FILE,
                 alpha: float = 0.0):
        K, dist, calib_size, self.rms = load_calibration(calibration_file)

        # The calibration was done at another resolution -> adapt K
        self.K = scale_intrinsics(K, calib_size, frame_size)
        self.dist = dist
        self.frame_size = frame_size

        # Camera matrix of the corrected image (same size as the input)
        self.new_K, _ = cv2.getOptimalNewCameraMatrix(
            self.K, self.dist, frame_size, alpha, frame_size)

        # Pre-computed pixel maps: for every output pixel, where to read
        # in the distorted input. CV_16SC2 is the fast fixed-point format.
        self.map_x, self.map_y = cv2.initUndistortRectifyMap(
            self.K, self.dist, None, self.new_K, frame_size, cv2.CV_16SC2)

    def __call__(self, frame: np.ndarray) -> np.ndarray:
        """Return the undistorted version of a frame."""
        h, w = frame.shape[:2]
        if (w, h) != self.frame_size:
            raise ValueError(f"Frame size {(w, h)} does not match the "
                             f"undistorter size {self.frame_size}")
        return cv2.remap(frame, self.map_x, self.map_y, cv2.INTER_LINEAR)


class Camera:
    """
    Small wrapper around cv2.VideoCapture that returns ready-to-use frames:
    undistorted and (optionally) mirrored.

    It can be used as a context manager so the camera is always released:

        with Camera() as cam:
            frame = cam.read()

    Parameters
    ----------
    index : int
        Camera index (0 is usually the built-in webcam).
    width, height : int
        Requested resolution. The real one is read back from the device
        because some cameras ignore the request.
    undistort : bool
        Apply the calibration correction.
    mirror : bool
        Flip horizontally after undistorting (selfie view).
    """

    def __init__(self, index: int = config.CAMERA_INDEX,
                 width: int = config.FRAME_WIDTH,
                 height: int = config.FRAME_HEIGHT,
                 undistort: bool = True,
                 mirror: bool = config.MIRROR):
        self.cap = cv2.VideoCapture(index, config.camera_backend())
        if not self.cap.isOpened():
            raise RuntimeError(f"Could not open the camera (index {index}).")

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        # Ask for 30 fps. Many webcams lower the frame rate on their own in
        # dim light (longer exposure), whatever is requested here.
        self.cap.set(cv2.CAP_PROP_FPS, config.CAMERA_FPS)
        real_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        real_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.frame_size = (real_w, real_h)
        if self.frame_size != (width, height):
            print(f"[camera] Requested {width}x{height}, got {real_w}x{real_h}")

        self.mirror = mirror
        self.undistorter: Optional[Undistorter] = (
            Undistorter(self.frame_size) if undistort else None)

    def read_raw(self) -> Optional[np.ndarray]:
        """Read a frame exactly as the camera gives it (or None if it fails)."""
        ok, frame = self.cap.read()
        return frame if ok else None

    def read(self) -> Optional[np.ndarray]:
        """
        Read a processed frame: undistort first, then mirror.

        The order matters: the distortion model was estimated on the real
        sensor image, so flipping before undistorting would apply the
        correction to the wrong side of the image.
        """
        frame = self.read_raw()
        if frame is None:
            return None
        if self.undistorter is not None:
            frame = self.undistorter(frame)
        if self.mirror:
            frame = cv2.flip(frame, 1)
        return frame

    def release(self) -> None:
        """Free the camera device."""
        self.cap.release()

    def __enter__(self) -> "Camera":
        return self

    def __exit__(self, *exc) -> None:
        self.release()


class FrameGrabber:
    """
    Read the camera in a background thread and keep only the newest frame.

    Without it, the loop waits for the camera (reading + undistorting) and
    then for the processing, one after the other. With it both happen at
    the same time and the processing always gets the most recent frame.

    Moved here from segmentation_preview (step 10) so the unlock loop and
    the preview share it. Call stop() before releasing the camera.
    """

    def __init__(self, cam) -> None:
        self.cam = cam
        self.frame: Optional[np.ndarray] = None
        self.count = 0                    # frames delivered by the camera
        self.running = True
        self._lock = threading.Lock()
        self._new = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        while self.running:
            frame = self.cam.read()
            if frame is None:
                self.running = False
                break
            with self._lock:
                self.frame = frame
                self.count += 1
            self._new.set()

    def read(self, timeout: float = 2.0) -> Optional[np.ndarray]:
        """Newest frame not returned yet (waits for it), or None if the camera stopped."""
        if not self._new.wait(timeout) or not self.running:
            return None
        with self._lock:
            self._new.clear()
            return self.frame

    def stop(self) -> None:
        self.running = False
        self._thread.join(timeout=1.0)
