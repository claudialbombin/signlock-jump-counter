"""
SignLock + Jump Counter - entry point.

    python main.py                 # unlock with H-O-L-A, then the jump counter
    python main.py --log           # also save the unlock attempts (step 11)
    python main.py --code HO       # shorter code, to test quickly

Flow (block diagram of the assignment):

    camera (calibrated, mirrored)
        -> security block: fingerspell H-O-L-A in LSE      (lse_auth)
        -> only once it is unlocked: jump counter / tracker (Tere's block)

Both blocks share the same camera (one FrameGrabber thread) and the same
window, so the camera is opened only once and the switch is seamless.

Contract with the tracker
-------------------------
run_tracker(grabber, window) is called once the code has been spelled. It
reads frames with grabber.read() (BGR, undistorted, mirrored; None if the
camera stopped), draws in `window` with cv2.imshow and returns when the
user quits. Replace the placeholder below with the call to the tracker.
"""

import argparse

import cv2

from lse_auth import config
from lse_auth.camera import Camera, FrameGrabber
from lse_auth.security import default_log_path, draw_fps, run_unlock

WINDOW = "SignLock + Jump Counter"


def run_tracker(grabber: FrameGrabber, window: str) -> None:
    """
    Jump counter (Tere's block). PLACEHOLDER until the tracker is ready:
    it only shows the camera with "ACCESO CONCEDIDO" so the whole flow can
    be tested. q / ESC to quit.
    """
    import time
    fps, last = 0.0, time.perf_counter()
    while True:
        frame = grabber.read()
        if frame is None:
            return
        view = frame.copy()
        cv2.rectangle(view, (20, 20), (560, 80), (0, 200, 0), -1)
        cv2.putText(view, "ACCESO CONCEDIDO", (35, 65), cv2.FONT_HERSHEY_SIMPLEX,
                    1.3, (255, 255, 255), 3, cv2.LINE_AA)
        cv2.putText(view, "Aqui empieza el contador de saltos (pendiente)", (20, 120),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
        now = time.perf_counter()
        fps = 0.9 * fps + 0.1 / max(now - last, 1e-6)
        last = now
        draw_fps(view, fps)
        cv2.imshow(window, view)
        if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
            return


def main() -> None:
    parser = argparse.ArgumentParser(description="SignLock + Jump Counter")
    parser.add_argument("--code", default="".join(config.UNLOCK_SEQUENCE),
                        help="unlock code (default HOLA)")
    parser.add_argument("--log", action="store_true",
                        help="save every unlock event in pasos/lse/pruebas/ (step 11)")
    args = parser.parse_args()

    log_path = default_log_path() if args.log else None
    with Camera() as cam:
        grabber = FrameGrabber(cam)
        cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL)
        try:
            if run_unlock(grabber, WINDOW, code=args.code.upper(), log_path=log_path):
                run_tracker(grabber, WINDOW)
        finally:
            grabber.stop()
            cv2.destroyAllWindows()
    if log_path:
        print(f"Unlock events saved in {log_path}")


if __name__ == "__main__":
    main()
