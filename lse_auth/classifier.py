"""
Step 6 - Rule-based classifier for H, O, L and A.

Everything that is not one of the four letters returns None ("no
letter"), which is the safe answer for the sequence decoder: it is better
to miss a frame than to accept a wrong letter.

The rules look at the STRUCTURE of the hand, not at absolute angles or
absolute sizes (both change from one person to another, with the wrist
and with the distance to the camera):

1. THUMB: the last finger (largest angle: with the right hand and the
   mirrored image it is on the left) is the extended thumb when it is
   THUMB_GAP..THUMB_MAX_GAP degrees away from its neighbour and thin
   (THUMB_MAX_WIDTH). With the
   thumb extended the thumb-index angle is usually wide; the other fingers
   are much closer to each other. If the index points up and the thumb
   too, the gap can drop to ~46 deg; then a gap of SHORT_THUMB_GAP is
   enough when the tip is clearly SHORTER than its neighbour (thumb /
   index measured 0.63-0.85, while in an O the leftmost tip is the middle
   finger, the longest: 0.99-1.18). In the O the "last finger" may be the
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
    O  an O-circle hole + at least 2 fingertips besides the circle
       (with the hole, extra short tips around the circle are tolerated),
       or, without the hole (seen from the front the circle is often not
       visible), no thumb and the three fingers CLOSE together:
         3 fingertips spread over at most O_MAX_SPAN degrees, or
         2 fingertips at most O_PAIR_MAX_GAP apart, one of them twice as
         wide as the other (two of them pressed together).
       At least one of the fingertips must be thin (FINGER_MAX_WIDTH): the
       bumps of a fist are not fingers.
       (The closeness was added with the NONE images: an open hand with the
       palm to the camera has its thumb on the other side, so "no thumb +
       3 tips" alone read 8 of 25 of them as O. Their tips are 39-41 deg
       apart (2 tips) or spread 45-134 deg (3 tips); the O without hole
       measured 20 deg (2 tips) and 30 deg (3 tips).)
    A  no finger at all, compact (solidity >= A_MIN_SOLIDITY) and nothing
       reaching far above the palm (top_extent <= A_MAX_TOP_EXTENT): the
       knuckles of a fist are right on top of the palm (1.22-1.51 palm
       radii), while an open hand whose fingers are not found (pressed
       together or blurred by movement) still reaches 1.58+.

If the hand leaves the ROI above the palm (features.cut) nothing is
returned: with a finger cut by the box an H looks like an L.

The two fingers of an H that are apart must both be single fingers
(<= FINGER_MAX_WIDTH): with one of them twice as wide it is three fingers
plus the thumb (an open hand), not an H. Two tips less than
H_SAME_PAIR_GAP apart are the pressed pair seen as two bumps, and count
as an H whatever their width.

Measured (widths in palm radii, angles in degrees):
    L  Tere: index 0.45-0.55 at 92-97 deg, thumb gap ~65
       Claudia: index 0.45-0.60 at 94-114 deg, thumb 0.23-0.63
    H  Tere: fingers apart at ~20 and ~45 deg, thumb gap ~68
       Claudia: fingers together 0.80-0.92 at 36-40 deg; fingers apart
       with index and thumb up: index 73 deg, thumb 119 deg (gap 46),
       thumb length 0.78 of the index
    A  Claudia: fist with the arm from below, 0 fingers, solidity
       0.78-0.85, top_extent 1.22-1.51
    O  Tere: 3 tips (gaps ~35, ~22) + circle hole at ~139 deg
       Claudia from the front: 3 tips 15 deg apart, no hole
       Claudia turned: 3 tips + circle tip at ~171 deg + hole at ~150 deg
"""

from typing import List, Optional, Tuple

from lse_auth.features import Finger, HandFeatures

THUMB_GAP = 50.0           # thumb-index measured 63-95
SHORT_THUMB_GAP = 35.0     # ...or this much if the tip is also clearly shorter:
THUMB_MAX_LENGTH_RATIO = 0.9  # thumb/index length 0.63-0.85, O leftmost tip 0.99-1.18
THUMB_MAX_GAP = 130.0      # wider than this is not a hand (e.g. a strip of wall)
THUMB_MAX_WIDTH = 0.8      # palm radii; thumbs measured 0.46-0.63, knuckles of a fist ~1.5
SINGLE_MAX_WIDTH = 0.65    # one finger measured 0.45-0.60 palm radii
PAIR_MIN_WIDTH = 0.75      # two fingers pressed together measured 0.79-0.92
SIDEWAYS_MAX_ANGLE = 70.0  # in between, a finger pointing to the side is the H pair
O_PAIR_RATIO = 1.6         # in an O with 2 tips, one is a pair if this much wider
H_MAX_GAP = 45.0           # index-middle measured ~25
H_SAME_PAIR_GAP = 15.0     # closer tips are the pressed pair seen as two bumps (measured 10)
FINGER_MAX_WIDTH = 0.8     # an O needs at least one finger this thin (fist bumps ~1.5)
O_MAX_SPAN = 38.0          # 3 O tips measured 30 deg; open hands 45-134
O_PAIR_MAX_GAP = 30.0      # 2 O tips measured 20 deg; open hands 39-41
A_MIN_SOLIDITY = 0.75      # fist 0.78-0.85
A_MAX_TOP_EXTENT = 1.55    # fist 1.22-1.51 palm radii; open or blurred hand without tips 1.58+


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
    gap = last.angle - previous.angle
    wide_gap = THUMB_GAP <= gap <= THUMB_MAX_GAP
    short_thumb = (SHORT_THUMB_GAP <= gap < THUMB_GAP
                   and last.length <= THUMB_MAX_LENGTH_RATIO * previous.length)
    if (wide_gap or short_thumb) and last.width <= THUMB_MAX_WIDTH:
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
        if not others:
            if (not features.o_hole and features.solidity >= A_MIN_SOLIDITY
                    and features.top_extent <= A_MAX_TOP_EXTENT):
                return "A"         # closed fist
            return None
        if min(f.width for f in others) > FINGER_MAX_WIDTH:
            return None            # only fat bumps (a fist): no real finger
        if features.o_hole and len(others) >= 2:
            return "O"
        span = others[-1].angle - others[0].angle
        if len(others) == 3 and span <= O_MAX_SPAN:
            return "O"
        if len(others) == 2 and span <= O_PAIR_MAX_GAP:
            narrow, wide = sorted(f.width for f in others)
            if wide >= O_PAIR_RATIO * narrow:
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
    if len(others) == 2 and others[1].angle < SIDEWAYS_MAX_ANGLE + 10:
        gap = others[1].angle - others[0].angle
        if gap <= H_SAME_PAIR_GAP:
            return "H"             # the pressed pair seen as two bumps
        if gap < H_MAX_GAP and max(f.width for f in others) <= FINGER_MAX_WIDTH:
            return "H"             # two single fingers apart, to the side (a "V" up is not H)
    return None
