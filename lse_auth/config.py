import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CALIBRATION_DIR = os.path.join(PROJECT_ROOT, "calibration")
CALIBRATION_FILE = os.path.join(CALIBRATION_DIR, "camera_params.npz")
REFERENCE_DIR = os.path.join(PROJECT_ROOT, "pasos", "lse", "referencia_lse")
DATASET_DIR = os.path.join(PROJECT_ROOT, "pasos", "lse", "dataset_lse")

# camara
CAMERA_INDEX = 0
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
CAMERA_FPS = 30
MIRROR = True   # espejo, siempre despues de quitar la distorsion


def camera_backend():
    import cv2
    if sys.platform == "darwin":
        return cv2.CAP_AVFOUNDATION
    if sys.platform.startswith("win"):
        return cv2.CAP_DSHOW
    return cv2.CAP_ANY


# recuadro de la mano (x, y, w, h en fraccion del frame)
# a la derecha xq signamos con la derecha y la imagen esta en espejo
HAND_ROI = (0.55, 0.15, 0.35, 0.70)


def roi_pixels(frame_width, frame_height):
    fx, fy, fw, fh = HAND_ROI
    return (int(fx * frame_width), int(fy * frame_height),
            int(fw * frame_width), int(fh * frame_height))


# segmentacion (paso 3), ajustado con las fotos de bg_01
BG_FRAMES = 30
BG_WEIGHT_Y = 0.5      # la Y pesa menos, la exposicion y las sombras cambian sobre todo la Y
BG_THRESHOLD = 25
SKIN_LOWER = (0, 135, 85)
SKIN_UPPER = (255, 180, 135)   # Cb hasta 135 xq con esta luz la piel clara llega a ~126
OPEN_KERNEL = 5
CLOSE_KERNEL = 9
FG_CLOSE_KERNEL = 31

# estabilizador (paso 7), en segundos xq los fps cambian segun el portatil
STABLE_CONFIRM_TIME = 0.5
STABLE_MIN_SHARE = 0.8
STABLE_MIN_FRAMES = 6
STABLE_RESET_TIME = 0.3

# decodificador (paso 8)
UNLOCK_SEQUENCE = ("H", "O", "L", "A")
SEQUENCE_TIMEOUT = 30.0
