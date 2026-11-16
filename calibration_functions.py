import cv2
import glob
import os
import copy
import numpy as np
from typing import List

# Load images from a given folder
def load_images(filenames: List) -> List:
    return [cv2.imread(filename) for filename in filenames]


# Find corners with cv2.findChessboardCorners and refine with cv2.cornerSubPix
def get_gray_images(imgs: List) -> List:
    # cv2.cornerSubPix() needs grayscale images
    return [cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) for img in imgs]


def find_corners(imgs: List, chessboard_shape: tuple) -> List:
    # Each element is a tuple (detected, corner)
    return [cv2.findChessboardCorners(img, chessboard_shape) for img in imgs]


def refine_corners(imgs_gray: List, corners: List) -> List:
    corners_copy = copy.deepcopy(corners)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.01)
    corners_refined = [cv2.cornerSubPix(img, corners_copy[i][1], (5, 5), (-1, -1), criteria) if corners_copy[i][0] else corners_copy[i][1] for i, img in enumerate(imgs_gray)]
    return corners_refined


# Draw corners, show and save images
def draw_corners(imgs: List, chessboard_shape: tuple, corners: List, corners_refined: List) -> List:
    imgs_copy = copy.deepcopy(imgs)
    imgs_copy_refined = [cv2.drawChessboardCorners(image, chessboard_shape, corners_refined[i], True) if corners[i][0] else image for i, image in enumerate(imgs_copy)]
    return imgs_copy_refined


def show_image(img: np.array, img_name: str = "Image"):
    cv2.imshow(img_name, img)
    cv2.waitKey()
    cv2.destroyAllWindows()


def write_image(output_folder: str, img_name: str, img: np.array):
    os.makedirs(output_folder, exist_ok=True)
    img_path = os.path.join(output_folder, img_name)
    cv2.imwrite(img_path, img)

# 3D Coordinates of the chessboard corners 
def get_chessboard_points(chessboard_shape, dx, dy):
    N = chessboard_shape[0] * chessboard_shape[1]
    array = np.zeros((N, 3), dtype=np.float32)
    for c in range(chessboard_shape[1]):
        for l in range(chessboard_shape[0]):
            indice = c * chessboard_shape[0] + l
            array[indice] = [dx * c, dy * l, 0]
    return array


# Calibration function using cv2.calibrateCamera
def calibrate(imgs_gray: List, corners: List, corners_refined: List, chessboard_shape: tuple, dx: float, dy: float):
    # Puntos 3D y 2D solo de las imágenes con detección correcta
    chessboard_points = [get_chessboard_points(chessboard_shape, dx, dy) for corner in corners if corner[0]]
    valid_corners = [corners_refined[i] for i, corner in enumerate(corners) if corner[0]]
    valid_corners = np.array(valid_corners, dtype=np.float32)

    rms, intrinsics, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(chessboard_points, valid_corners, imgs_gray[0].shape[::-1], None, None)

    # Extrínsecos
    extrinsics = list(map(lambda rvec, tvec: np.hstack((cv2.Rodrigues(rvec)[0], tvec)), rvecs, tvecs))
    return rms, intrinsics, dist_coeffs, rvecs, tvecs, extrinsics, chessboard_points, valid_corners


def per_image_error(points, corners_valid, K, D, rvecs, tvecs):
    # Error RMS de reproyección de cada imagen
    errs = []
    for p3d, p2d, r, t in zip(points, corners_valid, rvecs, tvecs):
        proj, _ = cv2.projectPoints(p3d, r, t, K, D)
        errs.append(np.sqrt(((proj - p2d) ** 2).sum(-1).mean()))
    return np.array(errs)