# paso 9: lo que se ve en pantalla mientras deletreas
# las letras que faltan NO se escriben, es una contraseña
# (putText no tiene tildes, por eso "intentalo")

import time

import cv2

from lse_auth import config
from lse_auth.sequence_decoder import Event
from lse_auth.stabilizer import State

MESSAGE_TIME = 2.5

RED = (0, 0, 230)
GREEN = (0, 200, 0)
ORANGE = (0, 165, 255)
YELLOW = (0, 230, 255)
GREY = (170, 170, 170)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

FONT = cv2.FONT_HERSHEY_SIMPLEX
MESSAGES = {
    Event.WRONG: "Secuencia incorrecta, intentalo de nuevo",
    Event.TIMEOUT: "Tiempo agotado, empieza de nuevo",
}


def _text(img, text, org, scale, color, thick=2):
    # con borde negro para que se lea sobre cualquier fondo
    cv2.putText(img, text, org, FONT, scale, BLACK, thick + 4, cv2.LINE_AA)
    cv2.putText(img, text, org, FONT, scale, color, thick, cv2.LINE_AA)


def _draw_status(img, unlocked):
    if unlocked:
        text, color = "DESBLOQUEADO", GREEN
    else:
        text, color = "BLOQUEADO", RED
    (tw, th), _ = cv2.getTextSize(text, FONT, 1.3, 3)
    cv2.rectangle(img, (20, 20), (50 + tw, 50 + th), color, -1)
    cv2.putText(img, text, (35, 35 + th), FONT, 1.3, WHITE, 3, cv2.LINE_AA)


def _draw_code(img, decoder, now):
    size = 64
    x0, y0 = 20, 100
    done = len(decoder.buffer)
    for i in range(len(decoder.code)):
        x = x0 + i * (size + 12)
        if i < done:
            color, th = GREEN, 3
        elif i == done and not decoder.is_unlocked():
            color, th = YELLOW, 3   # la siguiente
        else:
            color, th = GREY, 2
        cv2.rectangle(img, (x, y0), (x + size, y0 + size), BLACK, th + 3)
        cv2.rectangle(img, (x, y0), (x + size, y0 + size), color, th)
        if i < done:
            l = decoder.buffer[i]
            (tw, tht), _ = cv2.getTextSize(l, FONT, 1.6, 4)
            _text(img, l, (x + (size - tw) // 2, y0 + (size + tht) // 2), 1.6, GREEN, 4)
    left = decoder.time_left(now)
    if left is not None:
        _text(img, f"{left:.0f} s", (x0, y0 + size + 32), 0.8, WHITE)


def _draw_message(img, decoder, now):
    last = decoder.last_event
    if last is None or last[1] not in MESSAGES or now - last[0] > MESSAGE_TIME:
        return
    msg = MESSAGES[last[1]]
    (tw, _), _ = cv2.getTextSize(msg, FONT, 1.0, 2)
    _text(img, msg, ((img.shape[1] - tw) // 2, img.shape[0] - 30), 1.0, RED)


def _draw_hand(img, hand, roi, letter, detector, cut):
    x, y, w, _ = roi
    confirmed = False
    if detector.state in (State.CONFIRMED, State.WAITING_RESET):
        confirmed = letter is not None and letter == detector.confirmed
    color = GREEN if confirmed else ORANGE

    if hand is not None:
        cv2.drawContours(img, [hand.contour], -1, color, 2, cv2.LINE_8)
        bx, by, bw, bh = hand.bbox
        cv2.rectangle(img, (bx, by), (bx + bw, by + bh), color, 1)

    tx, ty = x + w + 15, y + 60
    if letter is not None:
        _text(img, letter, (tx, ty), 2.0, GREEN if confirmed else GREY, 4)
    if detector.state == State.CONFIRMING:
        cv2.rectangle(img, (tx, ty + 20), (tx + 100, ty + 32), WHITE, 1)
        cv2.rectangle(img, (tx, ty + 20), (tx + int(100 * detector.progress), ty + 32), GREEN, -1)
    if cut:
        _text(img, "Mete toda la mano en el recuadro", (x, y - 12), 0.7, RED)


def draw_overlay(view, hand, letter, detector, decoder, cut=False, now=None):
    if now is None:
        now = time.monotonic()
    roi = config.roi_pixels(view.shape[1], view.shape[0])
    x, y, w, h = roi
    cv2.rectangle(view, (x, y), (x + w, y + h), GREEN if decoder.is_unlocked() else WHITE, 2)
    _draw_hand(view, hand, roi, letter, detector, cut)
    _draw_status(view, decoder.is_unlocked())
    _draw_code(view, decoder, now)
    _draw_message(view, decoder, now)
    return view
