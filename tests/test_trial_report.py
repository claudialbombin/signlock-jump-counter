# tabla del paso 11 con logs escritos a mano

from lse_auth.trial_report import markdown_table, parse_session, summarise, tag_of

HEADER = "wall_time,t,event,letter,progress\n"


def write_log(tmp_path, rows, name="sesion_20261124_100000_natural.csv"):
    path = tmp_path / name
    lines = [f"2026-11-24 10:00:00,{t},{event},{letter},-" for t, event, letter in rows]
    path.write_text(HEADER + "\n".join(lines) + "\n")
    return str(path)


def test_tag_from_file_name():
    assert tag_of("pasos/lse/pruebas/sesion_20261124_100000_luz-natural.csv") == "luz-natural"
    assert tag_of("sesion_20261124_100000.csv") == ""


def test_one_clean_unlock(tmp_path):
    path = write_log(tmp_path, [(1.0, "correct", "H"), (3.0, "correct", "O"),
                                (5.0, "correct", "L"), (7.5, "unlocked", "A")])
    r = summarise([parse_session(path)])
    assert (r["attempts"], r["unlocked"], r["false_resets"], r["misread"]) == (1, 1, 0, 0)
    assert r["time_mean"] == 6.5


def test_wrong_letter_is_a_false_reset_and_a_misread(tmp_path):
    path = write_log(tmp_path, [(1.0, "correct", "H"), (3.0, "wrong", "L"),
                                (10.0, "correct", "H"), (12.0, "correct", "O"),
                                (14.0, "correct", "L"), (16.0, "unlocked", "A")])
    s = parse_session(path)
    r = summarise([s])
    assert (r["attempts"], r["unlocked"], r["false_resets"]) == (2, 1, 1)
    assert s.misread == {"O->L": 1}
    assert r["rate"] == 0.5


def test_restart_starts_a_new_attempt(tmp_path):
    path = write_log(tmp_path, [(1.0, "correct", "H"), (3.0, "correct", "O"),
                                (5.0, "restart", "H"), (7.0, "correct", "O"),
                                (9.0, "correct", "L"), (11.0, "unlocked", "A")])
    s = parse_session(path)
    assert [a.result for a in s.attempts] == ["restart", "unlocked"]
    assert s.misread == {"L->H": 1}
    assert s.attempts[1].duration == 6.0


def test_timeout_and_reset(tmp_path):
    path = write_log(tmp_path, [(1.0, "correct", "H"), (32.0, "timeout", ""),
                                (40.0, "correct", "H"), (42.0, "reset", ""),
                                (50.0, "wrong", "O")])
    s = parse_session(path)
    r = summarise([s])
    # el del reset no cuenta
    assert (r["attempts"], r["timeouts"], r["unlocked"]) == (1, 1, 0)
    assert s.stray_wrong == 1 and not s.misread


def test_table_has_one_row_per_condition_and_a_total(tmp_path):
    a = parse_session(write_log(tmp_path, [(1.0, "unlocked", "A")], "sesion_20261124_100000_natural.csv"), code=("A",))
    b = parse_session(write_log(tmp_path, [(1.0, "wrong", "H")], "sesion_20261124_110000_tere.csv"), code=("A",))
    table = markdown_table({"natural": [a], "tere": [b]})
    assert "| natural | 1 | 1 | 1 | 100% |" in table
    assert "| tere |" in table and "**Total**" in table
    assert "A->H" not in table          # es suelta, no mal leida
    assert "| tere | 1 | 0 | 0 | - | 0 | 0 | 0 | 1 |" in table
