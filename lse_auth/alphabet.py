# letras que reconocemos y como deberian verse (paso 1)
# solo mano derecha, H estatica, la O es el circulo pulgar-indice + 3 dedos

UNLOCK_SEQUENCE = ("H", "O", "L", "A")
NO_SIGN = "NONE"
CLASS_LABELS = (NO_SIGN, "H", "O", "L", "A")   # el orden es la tecla en capture_dataset
DOMINANT_HAND = "right"


class HandShape:
    def __init__(self, letter, description, extended_fingers, has_hole,
                 thumb_apart, orientation, reference_image):
        self.letter = letter
        self.description = description
        self.extended_fingers = extended_fingers   # (min, max) puntas que esperamos
        self.has_hole = has_hole
        self.thumb_apart = thumb_apart
        self.orientation = orientation
        self.reference_image = reference_image


# ojo: "dedos" = puntas en la silueta, en la H indice y corazon salen como uno gordo
LETTERS = {
    "H": HandShape("H", "Index and middle fingers extended together pointing "
                        "sideways, the rest of the fingers closed (static version).",
                   (1, 2), False, False, "horizontal", "letra_H_signame.png"),
    "O": HandShape("O", "Thumb and index touching in a small circle (like 'OK'), "
                        "middle, ring and little fingers extended and apart.",
                   (2, 4), True, False, "vertical", "letra_O_foaps.png"),
    "L": HandShape("L", "Index finger up and thumb extended sideways at ~90 "
                        "degrees, the other fingers closed.",
                   (2, 2), False, True, "any", "letra_L_signame.png"),
    "A": HandShape("A", "Closed fist with the thumb resting on the side of the "
                        "fingers. Compact silhouette, no loose fingers.",
                   (0, 0), False, False, "any", "letra_A_signame.png"),
}


def key_to_label(key):
    i = key - ord("0")
    if 0 <= i < len(CLASS_LABELS):
        return CLASS_LABELS[i]
    return None
