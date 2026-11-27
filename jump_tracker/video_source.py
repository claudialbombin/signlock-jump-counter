"""
Single entry point for frames in the jump counter block.

File mode reuses the video reading of Lab 5 (partB-D, read_video):
cv2.VideoCapture + CAP_PROP_* + 'ret, frame = cap.read()'. The only change
is that frames are read one at a time instead of being stored in a list, 
because of the high cost of storing all frames in memory.

Live mode uses the Camera of lse_auth (undistorted + mirrored), since the
labs only worked with recorded videos. This is the ONLY file of
jump_tracker that imports lse_auth (step 13).

    live : VideoSource()           -> webcam
    file : VideoSource("clip.mp4") -> recorded clip (already undistorted)

read() always returns (frame, t), with t in seconds since the start.
"""

import argparse
import os
import time

import cv2
import numpy as np

from lse_auth.camera import Camera


class VideoSource:
    """
    Frames from the live camera or from a video file.

    Args:
        videopath (str): Path to the video file. None -> live camera.
    """

    def __init__(self, videopath=None):
        self.is_live = videopath is None

        if self.is_live:
            self.camera = Camera()
            self.frame_width, self.frame_height = self.camera.frame_size
            self.frame_rate = None              # unknown: it is measured live
            self.start_time = time.perf_counter()
        else:
            # Same steps as read_video() 
            self.cap = cv2.VideoCapture(videopath)
            if not self.cap.isOpened():
                raise RuntimeError(f"Error: Could not open the video file {videopath}")
            self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            # CAP_PROP_FPS returns 0.0 if the file does not store it -> 30
            self.frame_rate = self.cap.get(cv2.CAP_PROP_FPS) or 30.0
            self.frame_index = 0
            self.timestamps = None
            csvpath = timestamps_path(videopath)
            if os.path.exists(csvpath):
                # Column 1 = t (column 0 is the index); ndmin=1 so a one-frame clip still gives an array
                self.timestamps = np.loadtxt(csvpath, delimiter=",", skiprows=1,usecols=1, ndmin=1)

    def read(self):
        """
        Reads the next frame.

        Returns:
            tuple: A tuple containing:
                - frame (np.ndarray): The image, or None at the end of the video.
                - t (float): Time of the frame in seconds, or None at the end.
        """
        if self.is_live:
            frame = self.camera.read()
            if frame is None:
                return None, None
            return frame, time.perf_counter() - self.start_time

        ret, frame = self.cap.read()
        if not ret:
            return None, None
        if self.timestamps is not None and self.frame_index < len(self.timestamps):
            t = float(self.timestamps[self.frame_index])   # real time of the frame
        else:
            t = self.frame_index / self.frame_rate         # time from the frame number
        self.frame_index += 1
        return frame, t

    def release(self):
        """Frees the camera or the video file."""
        if self.is_live:
            self.camera.release()
        else:
            self.cap.release()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.release()


def preview(videopath=None):
    """
    Shows the frames with their time and prints the real FPS every second.

    Args:
        videopath (str): Path to the video file. None -> live camera.
    """
    with VideoSource(videopath) as source:
        print(f"Source: {'live camera' if source.is_live else videopath} "
              f"({source.frame_width}x{source.frame_height})")
        # Files are played at their real speed, as in Lab 5
        wait_time = 1 if source.is_live else int(1000 / source.frame_rate)

        frames_count, last_print = 0, time.perf_counter()
        while True:
            frame, t = source.read()
            if frame is None:
                break
            cv2.putText(frame, f"t = {t:.2f} s", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.imshow("Video", frame)

            frames_count += 1
            now = time.perf_counter()
            if now - last_print >= 1.0:
                print(f"{frames_count / (now - last_print):.1f} FPS")
                frames_count, last_print = 0, now

            key = cv2.waitKey(wait_time)
            if key == ord("q"):
                break
    cv2.destroyAllWindows()

def timestamps_path(videopath):
    """
    Path of the CSV with the real time of every frame of a recorded clip.

    Args:
        videopath (str): Path to the video file.

    Returns:
        str: Same path with '_timestamps.csv' instead of the extension.
    """
    return os.path.splitext(videopath)[0] + "_timestamps.csv"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Preview of VideoSource")
    parser.add_argument("--video", help="video file (default: live camera)")
    preview(parser.parse_args().video)