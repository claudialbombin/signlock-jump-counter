# decodificador del paso 8

import pytest

from lse_auth.sequence_decoder import Event, SequenceDecoder


def decoder(**kwargs):
    return SequenceDecoder(code="HOLA", timeout=20.0, verbose=False, **kwargs)


def feed_all(dec, letters, start=0.0, step=1.0):
    return [dec.feed(letter, now=start + i * step) for i, letter in enumerate(letters)]


def test_right_order_unlocks():
    dec = decoder()
    events = feed_all(dec, "HOLA")
    assert events == [Event.CORRECT] * 3 + [Event.UNLOCKED]
    assert dec.is_unlocked() and dec.progress_text == "H-O-L-A" and dec.expected is None


def test_wrong_letter_empties_the_buffer():
    dec = decoder()
    assert feed_all(dec, "HOO") == [Event.CORRECT, Event.CORRECT, Event.WRONG]
    assert dec.buffer == [] and not dec.is_unlocked()
    feed_all(dec, "HOLA", start=10)
    assert dec.is_unlocked()


def test_wrong_order_never_unlocks():
    dec = decoder()
    feed_all(dec, "OHLA")
    assert not dec.is_unlocked()
    feed_all(dec, "HLOA", start=10)
    assert not dec.is_unlocked()


def test_first_letter_restarts_the_sequence():
    dec = decoder()
    assert feed_all(dec, "HOH") == [Event.CORRECT, Event.CORRECT, Event.RESTART]
    assert dec.progress_text == "H-_-_-_"
    feed_all(dec, "OLA", start=10)
    assert dec.is_unlocked()


def test_timeout_forgets_a_started_sequence():
    dec = decoder()
    feed_all(dec, "HO")
    assert dec.tick(now=15.0) is None and dec.time_left(now=15.0) == pytest.approx(6.0)
    assert dec.tick(now=30.0) is Event.TIMEOUT and dec.buffer == []
    # una letra despues del timeout ya es otro intento
    dec2 = decoder()
    feed_all(dec2, "HO")
    assert dec2.feed("L", now=60.0) is Event.WRONG and dec2.buffer == []


def test_each_correct_letter_restarts_the_timeout():
    dec = decoder()
    feed_all(dec, "HOLA", step=15.0)          # 45 s en total pero 15 entre letras
    assert dec.is_unlocked()


def test_unlocked_ignores_letters_until_reset():
    dec = decoder()
    feed_all(dec, "HOLA")
    assert dec.feed("O", now=10) is None and dec.is_unlocked()
    assert dec.tick(now=1000) is None and dec.is_unlocked()
    dec.reset(now=1001)
    assert not dec.is_unlocked() and dec.progress_text == "_-_-_-_"
    assert dec.last_event[1] is Event.RESET


def test_short_code_for_the_demo_without_a():
    dec = SequenceDecoder(code="HOL", verbose=False)
    feed_all(dec, "HOL")
    assert dec.is_unlocked()


def test_events_are_logged():
    dec = decoder()
    feed_all(dec, "HX")
    assert [e for _, e, _ in dec.events] == [Event.CORRECT, Event.WRONG]
    assert dec.last_event == (1.0, Event.WRONG, "X")
