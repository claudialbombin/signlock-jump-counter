# SignLock + Jump Counter

Final project for *Visión por Ordenador I* (iMAT, ICAI 2026/27).

The system has two blocks:

1. **Security block (SignLock)** – the user unlocks the system by fingerspelling
   **H-O-L-A** with the Spanish Sign Language (LSE) manual alphabet in front of
   the camera. Classical computer vision only: skin segmentation, contours,
   geometric features and a rule-based classifier, followed by a sequence
   decoder that remembers up to 4 patterns.
2. **Proposed system** – a rope jump counter with a tracker that runs once the
   correct sequence has been entered.

## Repository layout

| Path | Content |
|------|---------|
| `calibration_main.py`, `calibration_functions.py` | Offline camera calibration (chessboard) |
| `calibration_images/`, `Results/` | Calibration images and corner/reprojection results |
| `calibration/` | Exported camera parameters (`camera_params.npz`) |
| `lse_auth/` | Sign language authentication package (security block) |
| `pasos/lse/` | Work plan for the security block (one markdown file per step) + LSE reference images and dataset |
| `pasos/tracker/` | Work plan for the jump-counter tracker block (one markdown file per step) |

## Setup

```bash
pip install -r requirements.txt
```

## Usage

Run the whole system: spell H-O-L-A in front of the camera to unlock, then the jump counter starts.

```bash
python main.py               # unlock, then the tracker
python main.py --log         # also save the unlock events in pasos/lse/pruebas/
python main.py --trials --log --tag natural   # test session: unlock again and again, no tracker
python -m lse_auth.trial_report               # results table from the test sessions
```

Tools for each step:

```bash
python calibration_main.py                    # offline calibration -> calibration/camera_params.npz
python -m lse_auth.reference_viewer           # H-O-L-A reference panel
python -m lse_auth.capture_dataset            # capture the labelled dataset
python -m lse_auth.capture_dataset --summary  # images per class + contact sheet
python -m lse_auth.segmentation_preview       # live hand segmentation (f = background)
python -m lse_auth.segmentation_preview --dataset  # segment every image with a background
python -m pytest tests                        # unit tests of the security block
```
