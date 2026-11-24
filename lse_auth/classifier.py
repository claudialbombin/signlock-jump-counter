# paso 6: reglas para H, O, L, A. Si no es ninguna -> None
# (mejor perder un frame que aceptar una letra mala)
# las medidas de donde salen los umbrales estan en pasos/lse/06_clasificador_reglas.md

THUMB_GAP = 50.0
SHORT_THUMB_GAP = 35.0          # con indice y pulgar hacia arriba baja a ~46
THUMB_MAX_LENGTH_RATIO = 0.9    # pulgar/indice 0.63-0.85, en la O el de la izq mide 0.99-1.18
THUMB_MAX_GAP = 130.0
THUMB_MAX_WIDTH = 0.8
SINGLE_MAX_WIDTH = 0.65         # un dedo 0.45-0.60
PAIR_MIN_WIDTH = 0.75           # dos juntos 0.79-0.92
SIDEWAYS_MAX_ANGLE = 70.0
O_PAIR_RATIO = 1.6
H_MAX_GAP = 45.0
H_SAME_PAIR_GAP = 15.0
FINGER_MAX_WIDTH = 0.8
O_MAX_SPAN = 38.0               # O sin agujero: 30, manos abiertas 45-134
O_PAIR_MAX_GAP = 30.0           # O con 2 puntas: 20, manos abiertas 39-41
A_MIN_SOLIDITY = 0.75
A_MAX_TOP_EXTENT = 1.55


def split_thumb(features):
    # el pulgar es el ultimo dedo (el de mas a la izq) si esta bastante
    # separado del siguiente y es fino
    fingers = list(features.fingers)
    if len(fingers) < 2:
        return None, fingers
    last = fingers[-1]
    prev = fingers[-2]
    gap = last.angle - prev.angle
    wide = THUMB_GAP <= gap <= THUMB_MAX_GAP
    short = SHORT_THUMB_GAP <= gap < THUMB_GAP and last.length <= THUMB_MAX_LENGTH_RATIO * prev.length
    if (wide or short) and last.width <= THUMB_MAX_WIDTH:
        if features.o_hole:
            # no es el pulgar, es el circulo de la O que sobresale
            return None, fingers[:-1]
        return last, fingers[:-1]
    return None, fingers


def classify(features):
    if features.cut:
        return None   # con un dedo cortado la H parece una L
    thumb, others = split_thumb(features)

    if thumb is None:
        if len(others) == 0:
            if not features.o_hole and features.solidity >= A_MIN_SOLIDITY \
                    and features.top_extent <= A_MAX_TOP_EXTENT:
                return "A"
            return None
        if min(f.width for f in others) > FINGER_MAX_WIDTH:
            return None   # solo bultos gordos -> puño, no dedos
        if features.o_hole and len(others) >= 2:
            return "O"
        # O sin agujero (de frente muchas veces no se ve): dedos muy juntos
        span = others[-1].angle - others[0].angle
        if len(others) == 3 and span <= O_MAX_SPAN:
            return "O"
        if len(others) == 2 and span <= O_PAIR_MAX_GAP:
            w1, w2 = sorted(f.width for f in others)
            if w2 >= O_PAIR_RATIO * w1:
                return "O"
        return None

    if features.o_hole:
        return None

    if len(others) == 1:
        # una punta puede ser 1 dedo (L) o 2 pegados (H), lo dice el ancho
        f = others[0]
        if f.width >= PAIR_MIN_WIDTH:
            return "H"
        if f.width <= SINGLE_MAX_WIDTH:
            return "L"
        # en medio: la H apunta de lado, la L hacia arriba
        if f.angle < SIDEWAYS_MAX_ANGLE:
            return "H"
        return "L"

    if len(others) == 2 and others[1].angle < SIDEWAYS_MAX_ANGLE + 10:
        gap = others[1].angle - others[0].angle
        if gap <= H_SAME_PAIR_GAP:
            return "H"   # los dos dedos pegados vistos como dos bultos
        if gap < H_MAX_GAP and max(f.width for f in others) <= FINGER_MAX_WIDTH:
            return "H"
    return None
