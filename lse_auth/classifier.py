"""
Step 6 - Rule-based classifier (first version: H, O and L).

Only H, O and L are recognised for now: they are the letters with valid
images (A and NONE have to be recaptured, see PR #7). Everything else
returns None ("no letter"), which is the safe answer for the sequence
decoder: it is better to miss a frame than to accept a wrong letter.

The rules look at the STRUCTURE of the hand, not at absolute angles or
absolute sizes (both change from one person to another, with the wrist
and with the distance to the camera):

1. THUMB: the last finger (largest angle: with the right hand and the
   mirrored image it is on the left) is the extended thumb when it is
   THUMB_GAP..THUMB_MAX_GAP degrees away from its neighbour and thin
   (THUMB_MAX_WIDTH). With the
   thumb extended the thumb-index angle is always wide; the other fingers
   are much closer to each other. In the O the "last finger" may be the
   thumb-index circle sticking out: it is not a thumb when there is an
   O-circle hole.
2. The other fingers are counted. Two fingers pressed together give one
   fingertip, so its WIDTH (in palm radii, so it does not depend on the
   distance to the camera) tells one finger from two:
       <= SINGLE_MAX_WIDTH  one finger      (measured 0.45-0.60)
       >= PAIR_MIN_WIDTH    two fingers     (measured 0.79-0.92)
       in between           decided by the direction: the H fingers point
                            to the side, the L index points up.
   (Comparing with the width of the thumb was tried and dropped: seen
   from the side the thumb measures only 0.23-0.25, so a normal index
   looked like two fingers and the L was read as H.)

    L  thumb + 1 finger (the index)
    H  thumb + 2 fingers less than H_MAX_GAP apart pointing to the side,
       or thumb + 1 finger as wide as two
    O  no thumb + 3 fingertips (middle, ring, little finger),
       or no thumb + 2 fingertips when one of them is twice as wide as the
       other (two of them pressed together),
       or an O-circle hole + at least 2 fingertips besides the circle
       (with the hole, extra short tips around the circle are tolerated).
       The hole is not required: seen from the front, the circle is often
       not visible. At least one of the fingertips must be thin
       (FINGER_MAX_WIDTH): the bumps of a fist are not fingers.

If the hand leaves the ROI above the palm (features.cut) nothing is
returned: with a finger cut by the box an H looks like an L.

Measured (widths in palm radii, angles in degrees):
    L  Tere: index 0.45-0.55 at 92-97 deg, thumb gap ~65
       Claudia: index 0.45-0.60 at 94-114 deg, thumb 0.23-0.63
    H  Tere: fingers apart at ~20 and ~45 deg, thumb gap ~68
       Claudia: fingers together 0.80-0.92 at 36-40 deg
    O  Tere: 3 tips (gaps ~35, ~22) + circle hole at ~139 deg
       Claudia from the front: 3 tips 15 deg apart, no hole
       Claudia turned: 3 tips + circle tip at ~171 deg + hole at ~150 deg
"""

from typing import List, Optional, Tuple

from lse_auth.features import Finger, HandFeatures

THUMB_GAP = 50.0           # thumb-index measured 63-95
THUMB_MAX_GAP = 130.0      # wider than this is not a hand (e.g. a strip of wall)
THUMB_MAX_WIDTH = 0.8      # palm radii; thumbs measured 0.46-0.63, knuckles of a fist ~1.5
SINGLE_MAX_WIDTH = 0.65    # one finger measured 0.45-0.60 palm radii
PAIR_MIN_WIDTH = 0.75      # two fingers pressed together measured 0.79-0.92
SIDEWAYS_MAX_ANGLE = 70.0  # in between, a finger pointing to the side is the H pair
O_PAIR_RATIO = 1.6         # in an O with 2 tips, one is a pair if this much wider
H_MAX_GAP = 45.0           # index-middle measured ~25
FINGER_MAX_WIDTH = 0.8     # an O needs at least one finger this thin (fist bumps ~1.5)


def split_thumb(features: HandFeatures) -> Tuple[Optional[Finger], List[Finger]]:
    """
    Separate the extended thumb (if any) from the other fingers.

    Returns
    -------
    (thumb, others)
        thumb is None when it is not extended. When there is an O-circle
        hole, a finger in the thumb position is the circle and is dropped.
    """
    fingers = features.fingers
    if len(fingers) < 2:
        return None, list(fingers)
    last, previous = fingers[-1], fingers[-2]
    if (THUMB_GAP <= last.angle - previous.angle <= THUMB_MAX_GAP
            and last.width <= THUMB_MAX_WIDTH):
        if features.o_hole:
            return None, list(fingers[:-1])
        return last, list(fingers[:-1])
    return None, list(fingers)


def classify(features: HandFeatures) -> Optional[str]:
    """
    Letter shown by the hand, or None if it is not H, O or L.

    Parameters
    ----------
    features : HandFeatures
        Output of features.extract_features.
    """
    if features.cut:               # a finger leaves the box: do not guess
        return None
    thumb, others = split_thumb(features)

    if thumb is None:
        if not others or min(f.width for f in others) > FINGER_MAX_WIDTH:
            return None            # only fat bumps (a fist): no real finger
        if len(others) == 3 or (features.o_hole and len(others) >= 2):
            return "O"
        if len(others) == 2:
            narrow, wide = sorted(f.width for f in others)
            if features.o_hole or wide >= O_PAIR_RATIO * narrow:
                return "O"
        return None

    if features.o_hole:            # thumb extended and an O circle: contradictory
        return None
    if len(others) == 1:
        finger = others[0]
        if finger.width >= PAIR_MIN_WIDTH:
            return "H"
        if finger.width <= SINGLE_MAX_WIDTH:
            return "L"
        # In between: H points to the side, L points up (step 1 decisions)
        return "H" if finger.angle < SIDEWAYS_MAX_ANGLE else "L"
    if (len(others) == 2 and others[1].angle - others[0].angle < H_MAX_GAP
            and others[1].angle < SIDEWAYS_MAX_ANGLE + 10):
        return "H"                 # two fingers apart, to the side (a "V" up is not H)
    return None
