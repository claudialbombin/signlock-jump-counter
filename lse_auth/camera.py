import threading

import cv2

from lse_auth import config
from lse_auth.calibration_io import load_calibration, scale_intrinsics


class Undistorter:
    # los mapas se calculan una vez, cv2.undistort en cada frame iba lento
    def __init__(self, frame_size, calibration_file=config.CALIBRATION_FILE, alpha=0.0):
        K, dist, calib_size, self.rms = load_calibration(calibration_file)
        self.K = scale_intrinsics(K, calib_size, frame_size)
        self.dist = dist
        self.frame_size = frame_size
        # alpha 0 para que no salgan bordes negros
        self.new_K, _ = cv2.getOptimalNewCameraMatrix(self.K, dist, frame_size, alpha, frame_size)
        self.map_x, self.map_y = cv2.initUndistortRectifyMap(self.K, dist, None, self.new_K,
                                                             frame_size, cv2.CV_16SC2)

    def __call__(self, frame):
        h, w = frame.shape[:2]
        if (w, h) != self.frame_size:
            raise ValueError(f"Frame size {(w, h)} does not match the "
                             f"undistorter size {self.frame_size}")
        return cv2.remap(frame, self.map_x, self.map_y, cv2.INTER_LINEAR)


class Camera:
    def __init__(self, index=config.CAMERA_INDEX, width=config.FRAME_WIDTH,
                 height=config.FRAME_HEIGHT, undistort=True, mirror=config.MIRROR):
        self.cap = cv2.VideoCapture(index, config.camera_backend())
        if not self.cap.isOpened():
            raise RuntimeError(f"Could not open the camera (index {index}).")
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_FPS, config.CAMERA_FPS)

        w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.frame_size = (w, h)
        if self.frame_size != (width, height):
            print(f"[camera] Requested {width}x{height}, got {w}x{h}")

        self.mirror = mirror
        self.undistorter = None
        if undistort:
            self.undistorter = Undistorter(self.frame_size)

    def read_raw(self):
        ok, frame = self.cap.read()
        if not ok:
            return None
        return frame

    def read(self):
        frame = self.read_raw()
        if frame is None:
            return None
        if self.undistorter is not None:
            frame = self.undistorter(frame)
        if self.mirror:
            frame = cv2.flip(frame, 1)   # despues de undistort!
        return frame

    def release(self):
        self.cap.release()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.release()


class FrameGrabber:
    # hilo que lee la camara y se queda con el ultimo frame,
    # asi leer y procesar van a la vez
    def __init__(self, cam):
        self.cam = cam
        self.frame = None
        self.count = 0
        self.running = True
        self._lock = threading.Lock()
        self._new = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        while self.running:
            frame = self.cam.read()
            if frame is None:
                self.running = False
                break
            with self._lock:
                self.frame = frame
                self.count += 1
            self._new.set()

    def read(self, timeout=2.0):
        if not self._new.wait(timeout) or not self.running:
            return None
        with self._lock:
            self._new.clear()
            return self.frame

    def stop(self):
        self.running = False
        self._thread.join(timeout=1.0)
