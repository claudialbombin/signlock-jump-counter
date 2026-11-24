# SignLock + Jump Counter
#
# python main.py                               HOLA y luego el contador de saltos
# python main.py --code HO                     codigo mas corto para probar
# python main.py --trials --log --tag natural  sesiones del paso 11 (sin tracker)

import argparse
import time

import cv2

from lse_auth import config
from lse_auth.camera import Camera, FrameGrabber
from lse_auth.security import default_log_path, draw_fps, run_unlock

WINDOW = "SignLock + Jump Counter"


def run_tracker(grabber, window):
    # TODO Tere: cambiar esto por el tracker
    # grabber.read() da los frames ya sin distorsion y en espejo (None si se para la camara)
    fps = 0.0
    last = time.perf_counter()
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
        t = time.perf_counter()
        fps = 0.9 * fps + 0.1 / max(t - last, 1e-6)
        last = t
        draw_fps(view, fps)
        cv2.imshow(window, view)
        k = cv2.waitKey(1) & 0xFF
        if k == ord("q") or k == 27:
            return


def main():
    parser = argparse.ArgumentParser(description="SignLock + Jump Counter")
    parser.add_argument("--code", default="".join(config.UNLOCK_SEQUENCE),
                        help="unlock code (default HOLA)")
    parser.add_argument("--log", action="store_true",
                        help="save every unlock event in pasos/lse/pruebas/ (step 11)")
    parser.add_argument("--trials", action="store_true",
                        help="step 11 test session: lock again after every unlock, no tracker")
    parser.add_argument("--tag", help="test condition added to the log name (e.g. natural, tere)")
    args = parser.parse_args()

    code = args.code.upper()
    log_path = None
    if args.log:
        log_path = default_log_path(args.tag)

    with Camera() as cam:
        grabber = FrameGrabber(cam)   # una sola camara para los dos bloques
        cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL)
        try:
            if args.trials:
                while run_unlock(grabber, WINDOW, code=code, log_path=log_path):
                    pass
            elif run_unlock(grabber, WINDOW, code=code, log_path=log_path):
                run_tracker(grabber, WINDOW)
        finally:
            grabber.stop()
            cv2.destroyAllWindows()

    if log_path:
        print(f"Unlock events saved in {log_path}")
        print("Results table: python -m lse_auth.trial_report")


if __name__ == "__main__":
    main()
