"""
Records the reference videos of the jump counter (steps 1 and 2).

Frames come from VideoSource in live mode, i.e. from lse_auth's Camera:
already undistorted and mirrored, exactly what the tracker will see live.
The video is written as in Lab 5 (partB-D): cv2.VideoWriter with the
'mp4v' codec and the size of the frames.

Webcams do not keep a constant frame rate, so the fps stored in the video
is only used to play it back. The real time of every frame is saved in
<video>_timestamps.csv (index,t) and VideoSource reads it back.

Every press of r starts a new take: normal_01.mp4, normal_02.mp4...
Keys: r = start / stop a take, q = quit.

    python -m jump_tracker.record_reference --name normal
"""

import argparse
import os
import time

import cv2

from jump_tracker import config
from jump_tracker.video_source import VideoSource, timestamps_path

# Clip types: 'prueba' for step 1, the rest are the step 2 references
CLIP_TYPES = ["prueba", "normal", "lento", "pausa", "ruido"]

# Only used to play the video back; the real times go to the CSV
PLAYBACK_FPS = 30.0


def next_videopath(name):
    """
    Finds the first free take number for a clip type.

    Args:
        name (str): Clip type (normal, lento...).

    Returns:
        str: Path of the new video, e.g. .../videos_referencia/normal_02.mp4
    """
    if not os.path.exists(config.VIDEOS_DIR):
        os.makedirs(config.VIDEOS_DIR)
    take = 1
    while os.path.exists(os.path.join(config.VIDEOS_DIR, f"{name}_{take:02d}.mp4")):
        take += 1
    return os.path.join(config.VIDEOS_DIR, f"{name}_{take:02d}.mp4")


def stop_take(out, csv_file, videopath, n_frames, duration):
    """
    Closes the video and the CSV of a take and prints a summary.

    Args:
        out (cv2.VideoWriter): Writer of the take.
        csv_file (file): Open timestamps CSV.
        videopath (str): Path of the video (for the message).
        n_frames (int): Frames written.
        duration (float): Time of the last frame in seconds.
    """
    out.release()
    csv_file.close()
    mean_fps = (n_frames - 1) / duration if duration > 0 else 0.0
    print(f"Saved {os.path.basename(videopath)}: {n_frames} frames, "
          f"{duration:.1f} s, {mean_fps:.1f} FPS on average")


def record(name):
    """
    Shows the camera and records takes of the given type with r.

    Args:
        name (str): Clip type, used in the file name.
    """
    with VideoSource() as source:
        frame_size = (source.frame_width, source.frame_height)
        print(f"Camera {frame_size[0]}x{frame_size[1]}. r = record / stop, q = quit")

        # Only open while a take is being recorded
        out, csv_file, videopath = None, None, None
        n_frames, t_start, t_rec = 0, None, 0.0

        # FPS measured once per second, as in VideoSource.preview()
        fps, frames_count, last_print = 0.0, 0, time.perf_counter()

        while True:
            frame, t = source.read()
            if frame is None:
                print("Error: the camera stopped")
                break

            # Write the CLEAN frame (before drawing anything on it)
            if out is not None:
                if t_start is None:
                    t_start = t              # the first frame of the take is t = 0
                t_rec = t - t_start
                out.write(frame)
                csv_file.write(f"{n_frames},{t_rec:.4f}\n")
                n_frames += 1

            frames_count += 1
            now = time.perf_counter()
            if now - last_print >= 1.0:
                fps = frames_count / (now - last_print)
                frames_count, last_print = 0, now

            # Drawings only on a copy that is shown, never recorded
            view = frame.copy()
            cv2.putText(view, f"{fps:.1f} FPS", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            if out is not None:
                cv2.circle(view, (frame_size[0] - 30, 25), 10, (0, 0, 255), -1)
                cv2.putText(view, f"REC {t_rec:.1f} s", (frame_size[0] - 190, 35),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            cv2.imshow("Grabar referencia", view)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("r"):
                if out is None:
                    # Start a new take
                    videopath = next_videopath(name)
                    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                    out = cv2.VideoWriter(videopath, fourcc, PLAYBACK_FPS, frame_size)
                    if not out.isOpened():
                        raise RuntimeError(f"Error: could not create {videopath}")
                    csv_file = open(timestamps_path(videopath), "w")
                    csv_file.write("index,t\n")
                    n_frames, t_start, t_rec = 0, None, 0.0
                    print(f"Recording {os.path.basename(videopath)}...")
                else:
                    stop_take(out, csv_file, videopath, n_frames, t_rec)
                    out, csv_file = None, None
            elif key == ord("q"):
                break

        # Quitting in the middle of a take still saves it
        if out is not None:
            stop_take(out, csv_file, videopath, n_frames, t_rec)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Record reference clips (steps 1-2)")
    parser.add_argument("--name", choices=CLIP_TYPES, default="prueba",
                        help="clip type, used in the file name")
    record(parser.parse_args().name)