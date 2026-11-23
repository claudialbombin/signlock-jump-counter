"""
Tests of the step 6 rules with feature vectors measured on real frames.

Each case copies the fingers (angle, width, length), solidity and
top_extent printed by `segmentation_preview --errors` or the dataset
evaluation, so the rules are checked without the images.

Run with:  python -m pytest tests/test_classifier.py
"""

import pytest

from lse_auth.classifier import classify
from lse_auth.features import Finger, HandFeatures


def hand(fingers, solidity=0.7, top_extent=3.0, o_hole=False, cut=False):
    return HandFeatures(
        fingers=[Finger(tip=(0, 0), angle=a, width=w, length=l) for a, w, l in fingers],
        cut=cut, has_hole=o_hole, o_hole=o_hole,
        solidity=solidity, top_extent=top_extent)


CASES = [
    # letters
    ("L Tere", [(92.0, 0.47, 3.1), (157.0, 0.53, 2.3)], {}, "L"),
    ("H pressed Claudia", [(38.0, 0.85, 3.0), (128.0, 0.48, 2.2)], {}, "H"),
    ("H thumb up", [(39.7, 0.46, 2.62), (72.8, 0.46, 2.76), (119.1, 0.62, 2.17)], {}, "H"),
    ("H pair as two bumps", [(36.5, 0.83, 3.05), (46.9, 1.44, 2.77), (121.5, 0.47, 2.27)], {}, "H"),
    ("O Tere with hole", [(19.7, 0.41, 2.75), (57.0, 0.46, 3.0), (79.0, 0.45, 3.2),
                          (137.8, 1.47, 2.14)], {"o_hole": True}, "O"),
    ("O Claudia front", [(76.7, 1.64, 2.23), (91.5, 0.85, 2.75), (106.2, 0.66, 2.71)], {}, "O"),
    ("O Claudia 2 tips", [(59.8, 1.18, 2.26), (79.9, 0.72, 2.67)], {}, "O"),
    ("A fist", [], {"solidity": 0.82, "top_extent": 1.45}, "A"),
    # not letters (NONE frames that used to give O / H / A)
    ("open hand, 2 tips apart", [(46.3, 0.56, 2.06), (87.0, 1.0, 2.57)], {}, None),
    ("open hand, 3 tips spread", [(66.3, 0.64, 2.01), (98.0, 0.93, 2.73),
                                  (118.6, 0.57, 3.23)], {}, None),
    ("three fingers + thumb", [(58.2, 0.61, 3.97), (78.3, 1.19, 3.43),
                               (141.3, 0.74, 1.97)], {}, None),
    ("blurred open hand", [], {"solidity": 0.88, "top_extent": 1.66}, None),
    ("blurred hand at the limit", [], {"solidity": 0.89, "top_extent": 1.58}, None),
    ("loose blob", [], {"solidity": 0.6, "top_extent": 1.3}, None),
    ("cut by the box", [(92.0, 0.47, 3.1), (157.0, 0.53, 2.3)], {"cut": True}, None),
]


@pytest.mark.parametrize("name,fingers,extra,expected", CASES, ids=[c[0] for c in CASES])
def test_rules(name, fingers, extra, expected):
    assert classify(hand(fingers, **extra)) == expected
