import cv2
from typing import List
import numpy as np
import copy
import os
import glob
import matplotlib.pyplot as plt
import calibration_functions as cal_func
from lse_auth.calibration_io import save_calibration

# CONFIGURATION

# Folder with the calibration images (relative to this script or absolute path).
IMAGES_DIR = os.path.join("calibration_images")      

RESULTS_DIR = "Results"      # drawn corners and reprojection error plot
CHESSBOARD_SHAPE = (10, 7)   # INNER corners (columns, rows)
SQUARE_SIZE = 15             # mm 
SHOW_IMAGES = False          # True to display each image with its detected corners



def main():
    # Load images
    imgs_path = glob.glob(os.path.join(IMAGES_DIR, "*.jpg")) + glob.glob(os.path.join(IMAGES_DIR, "*.png"))
    imgs_path.sort()
    if not imgs_path:
        raise SystemExit(f"No images found in '{IMAGES_DIR}'.")
    imgs = cal_func.load_images(imgs_path)
    imgs_gray = cal_func.get_gray_images(imgs)
    print(f"{len(imgs)} images loaded from '{IMAGES_DIR}'")

    # Detect and refine corners
    corners = cal_func.find_corners(imgs, CHESSBOARD_SHAPE)
    corners_refined = cal_func.refine_corners(imgs_gray, corners)
    print(f"Chessboard detected in {sum(c[0] for c in corners)} of {len(imgs)} images")
    for path, c in zip(imgs_path, corners):
        if not c[0]:
            print("  No detection:", os.path.basename(path))

    # Check the detections visually
    imgs_drawn = cal_func.draw_corners(imgs, CHESSBOARD_SHAPE, corners, corners_refined)
    for i, image in enumerate(imgs_drawn):
        cal_func.write_image(RESULTS_DIR, f"Image_corners_ref_{i+1}.png", image)
        if SHOW_IMAGES:
            cal_func.show_image(image)

    # 3D chessboard points and calibration
    rms, intrinsics, dist_coeffs, rvecs, tvecs, extrinsics, chessboard_points, valid_corners = cal_func.calibrate(
        imgs_gray, corners, corners_refined, CHESSBOARD_SHAPE, SQUARE_SIZE, SQUARE_SIZE)

    print("\nIntrinsics:\n", intrinsics)
    print("Distortion coefficients:\n", dist_coeffs)
    print("Root mean squared reprojection error:\n", rms)

    # Save the parameters so the live system does not need to recalibrate
    image_size = imgs_gray[0].shape[::-1]   # (width, height)
    save_calibration(intrinsics, dist_coeffs, image_size, rms)
    print("Camera parameters saved for the live system (calibration/camera_params.npz)")

    # Reprojection error per image
    errors = cal_func.per_image_error(chessboard_points, valid_corners, intrinsics, dist_coeffs, rvecs, tvecs)
    names = [os.path.basename(p) for p, c in zip(imgs_path, corners) if c[0]]

    plt.figure(figsize=(10, 3.5))
    plt.bar(range(len(errors)), errors, color="tab:blue")
    plt.axhline(rms, color="r", ls="--", lw=0.8)
    plt.xticks(range(len(errors)), names, rotation=90)
    plt.ylabel("RMS error [px]")
    plt.title("Reprojection error per image")
    plt.grid(axis="y", alpha=0.4)
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, "reprojection_error.png"))
    plt.show()


if __name__ == "__main__":
    main()
    