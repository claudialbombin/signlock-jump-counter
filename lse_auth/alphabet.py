"""
Target alphabet of the security block: the LSE letters H, O, L and A.

This module is the "written down" version of step 1. It fixes which hand
shapes we want to recognise and what we expect them to look like once we only
have a binary silhouette of the hand. The later steps (feature extraction and
rule-based classifier) read these descriptions instead of inventing their own,
so if we ever change our mind about a letter we only change it here.

Decisions taken in step 1 (see pasos/01_definicion_alfabeto_lse.md):
    * Only the RIGHT hand, palm facing the camera, fingers pointing up.
      Accepting both hands would double the cases to tune; we can extend it
      later by mirroring the image if there is time.
    * H is treated as a STATIC posture (index + middle finger together,
      no wrist movement), which is much easier to detect with classical CV.
    * O is NOT a closed fist with a big hole: it is a small thumb-index
      circle with the other three fingers extended. So it needs BOTH a hole
      and ~3 extended fingers to be told apart from a relaxed open hand.

The numeric ranges below are first guesses taken from the reference images.
They will be tuned in steps 5, 6 and 11 with our own dataset (step 2).
"""

from dataclasses import dataclass
from typing import Dict, Tuple

# Word that unlocks the system, in order.
UNLOCK_SEQUENCE: Tuple[str, ...] = ("H", "O", "L", "A")

# Label used when the hand is not making any of the target letters
# (or there is no hand at all).
NO_SIGN = "NONE"

# Every class the classifier can output. The order also defines the
# keyboard shortcut used when capturing the dataset (0 = NONE, 1 = H...).
CLASS_LABELS: Tuple[str, ...] = (NO_SIGN, "H", "O", "L", "A")

# Hand accepted by the system ("right" or "left").
DOMINANT_HAND = "right"


@dataclass(frozen=True)
class HandShape:
    """
    Description of one LSE letter as a hand silhouette.

    Attributes
    ----------
    letter : str
        Letter of the alphabet ("H", "O", "L" or "A").
    description : str
        Short human description of the hand shape (used in the UI and report).
    extended_fingers : tuple of int
        (min, max) number of fingers we expect to see sticking out of the
        palm in the silhouette. The thumb counts when it is clearly separated.
    has_hole : bool
        True if the silhouette should contain an inner hole (a closed loop
        made by the fingers), which shows up as a child contour.
    thumb_apart : bool
        True if the thumb is clearly separated from the rest of the hand,
        forming a wide gap (big convexity defect), like in the L.
    elongated : bool
        True if the silhouette is clearly taller than wide (fingers up).
    reference_image : str
        File name of the reference picture inside pasos/referencia_lse/.
    """

    letter: str
    description: str
    extended_fingers: Tuple[int, int]
    has_hole: bool
    thumb_apart: bool
    elongated: bool
    reference_image: str


# Expected appearance of each letter. Counting "extended fingers" here means
# what a convexity-defects approach would count on the silhouette, not the
# anatomical fingers. For example, in H the index and middle finger are glued
# together so they will probably look like ONE wide finger.
LETTERS: Dict[str, HandShape] = {
    "H": HandShape(
        letter="H",
        description="Index and middle fingers extended and together, "
                    "the rest of the fingers closed (static version).",
        extended_fingers=(1, 2),
        has_hole=False,
        thumb_apart=False,
        elongated=True,
        reference_image="letra_H_signame.png",
    ),
    "O": HandShape(
        letter="O",
        description="Thumb and index touching in a small circle (like 'OK'), "
                    "middle, ring and little fingers extended and apart.",
        # 3 loose fingers, but two of them can merge in the silhouette and
        # the thumb-index loop may add a bump, so the range is tolerant.
        extended_fingers=(2, 4),
        has_hole=True,
        thumb_apart=False,
        elongated=True,
        reference_image="letra_O_foaps.png",
    ),
    "L": HandShape(
        letter="L",
        description="Index finger up and thumb extended sideways at ~90 "
                    "degrees, the other fingers closed.",
        extended_fingers=(2, 2),
        has_hole=False,
        thumb_apart=True,
        elongated=False,
        reference_image="letra_L_signame.png",
    ),
    "A": HandShape(
        letter="A",
        description="Closed fist with the thumb resting on the side of the "
                    "fingers. Compact silhouette, no loose fingers.",
        extended_fingers=(0, 0),
        has_hole=False,
        thumb_apart=False,
        elongated=False,
        reference_image="letra_A_signame.png",
    ),
}


def key_to_label(key: int) -> str:
    """
    Translate a keyboard key code ('0'..'4') into a class label.

    Parameters
    ----------
    key : int
        Key code as returned by cv2.waitKey() & 0xFF.

    Returns
    -------
    str or None
        The class label, or None if the key is not a valid class number.
    """
    index = key - ord("0")
    if 0 <= index < len(CLASS_LABELS):
        return CLASS_LABELS[index]
    return None


def _check_consistency() -> None:
    """Small sanity checks so a typo in the table above fails early."""
    assert set(UNLOCK_SEQUENCE) == set(LETTERS), "sequence and letters differ"
    assert len(UNLOCK_SEQUENCE) <= 4, "the decoder only remembers 4 patterns"
    for letter, shape in LETTERS.items():
        assert letter == shape.letter
        low, high = shape.extended_fingers
        assert 0 <= low <= high <= 5, f"bad finger range for {letter}"


_check_consistency()
