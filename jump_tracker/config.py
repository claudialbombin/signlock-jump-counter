"""
Global configuration for the jump counter block.

Every path and "magic number" of jump_tracker lives here, so the rest of
the modules import them instead of hard-coding values. Camera settings are
NOT repeated here: video_source.py uses the defaults of lse_auth's Camera.
"""

import os
import sys

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

# Root of the repository (the folder that contains this package).
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Reference videos recorded in step 2 (the .mp4 files are not in git).
VIDEOS_DIR = os.path.join(PROJECT_ROOT, "pasos", "tracker", "videos_referencia")

# Generated plots and CSVs (ignored by git).
RESULTS_DIR = os.path.join(PROJECT_ROOT, "pasos", "tracker", "results")

# ---------------------------------------------------------------------------
# Thresholds (filled in later, measured on the reference videos)
# ---------------------------------------------------------------------------

# Step 3 - black shoe segmentation (HSV)
# V_MAX = ...            # pixels darker than this can be the shoe

# Step 4 - shoe blob filtering
# MIN_AREA = ...         # px, smaller blobs are noise
# MAX_AREA = ...         # px, bigger blobs are shadows / furniture

# Step 6 - tracking
# LOST_FRAMES = ...      # frames without detection before state = LOST

# Step 10 - jump counting
# MIN_INTERVAL = ...     # s, minimum time between two jumps