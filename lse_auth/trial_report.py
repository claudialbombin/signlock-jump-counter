"""
Step 11 - Results table from the unlock logs.

`python main.py --trials --log --tag <condition>` saves every decoder event
of a test session in pasos/lse/pruebas/sesion_<date>_<condition>.csv. This
script reads those CSVs and builds the table of the report:

    python -m lse_auth.trial_report                      # every session
    python -m lse_auth.trial_report pasos/lse/pruebas/sesion_*_natural.csv
    python -m lse_auth.trial_report --out pasos/lse/pruebas/resultados.md

How an attempt is counted
-------------------------
During a test session the user is always trying to spell the code, so:

* An attempt starts with the first correct letter (or a restart).
* It ends with `unlocked` (success), `wrong` (a letter that was not the
  expected one: a false reset), `restart` (the first letter of the code
  arrived in the middle: the attempt is lost, a new one starts), `timeout`
  or `reset` (the r key: aborted, not counted in the rate).
* Every `wrong` or `restart` is a letter read wrongly, because the user was
  showing the expected one. The table says which letter was expected and
  which one was read (e.g. O->H).
"""

import argparse
import csv
import glob
import os
import statistics
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

from lse_auth import config

LOG_DIR = os.path.join(config.PROJECT_ROOT, "pasos", "lse", "pruebas")


@dataclass
class Attempt:
    start: float
    end: Optional[float] = None
    result: Optional[str] = None        # unlocked, wrong, restart, timeout, reset

    @property
    def duration(self) -> Optional[float]:
        return None if self.end is None else self.end - self.start


@dataclass
class Session:
    name: str
    tag: str
    attempts: List[Attempt] = field(default_factory=list)
    misread: Counter = field(default_factory=Counter)     # "O->H": count
    stray_wrong: int = 0                                  # wrong letter with no attempt open

    def count(self, result: str) -> int:
        return sum(a.result == result for a in self.attempts)

    @property
    def finished(self) -> List[Attempt]:
        """Attempts that count for the rate (not aborted with r, not left open)."""
        return [a for a in self.attempts if a.result not in (None, "reset")]


def tag_of(path: str) -> str:
    """sesion_20261124_101500_natural.csv -> 'natural' ('' if there is no tag)."""
    parts = os.path.splitext(os.path.basename(path))[0].split("_", 3)
    return parts[3] if len(parts) == 4 else ""


def parse_session(path: str, code: Sequence[str] = config.UNLOCK_SEQUENCE) -> Session:
    """Turn the event log of one session into attempts."""
    session = Session(name=os.path.basename(path), tag=tag_of(path))
    current: Optional[Attempt] = None
    typed = 0                                   # letters of the code already shown

    def close(t: float, result: str) -> None:
        nonlocal current, typed
        if current is not None:
            current.end, current.result = t, result
        current, typed = None, 0

    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            t, event, letter = float(row["t"]), row["event"], row["letter"]
            expected = code[typed] if typed < len(code) else None
            if event in ("correct", "unlocked"):
                if current is None:
                    current = Attempt(start=t)
                    session.attempts.append(current)
                typed += 1
                if event == "unlocked":
                    close(t, "unlocked")
            elif event == "restart":
                if current is not None:
                    session.misread[f"{expected}->{letter}"] += 1
                    close(t, "restart")
                current = Attempt(start=t)
                session.attempts.append(current)
                typed = 1
            elif event == "wrong":
                if current is None:
                    # wrong letter before starting: the first letter was misread
                    session.stray_wrong += 1
                    session.misread[f"{code[0]}->{letter}"] += 1
                else:
                    session.misread[f"{expected}->{letter}"] += 1
                    close(t, "wrong")
            elif event in ("timeout", "reset"):
                close(t, event)
    return session


def summarise(sessions: List[Session]) -> Dict[str, object]:
    """Numbers of the results table for a group of sessions."""
    finished = [a for s in sessions for a in s.finished]
    unlocked = [a for a in finished if a.result == "unlocked"]
    times = [a.duration for a in unlocked]
    misread = sum((s.misread for s in sessions), Counter())
    return {
        "sessions": len(sessions),
        "attempts": len(finished),
        "unlocked": len(unlocked),
        "rate": len(unlocked) / len(finished) if finished else None,
        "false_resets": sum(s.count("wrong") + s.count("restart") for s in sessions),
        "timeouts": sum(s.count("timeout") for s in sessions),
        "misread": sum(misread.values()),
        "misread_pairs": misread,
        "time_mean": statistics.mean(times) if times else None,
        "time_median": statistics.median(times) if times else None,
    }


def _fmt(value, pattern: str) -> str:
    return "-" if value is None else pattern.format(value)


def markdown_table(groups: Dict[str, List[Session]]) -> str:
    """One row per condition (tag) plus the total."""
    lines = [
        "| Condición | Sesiones | Intentos | Desbloqueos | Tasa | Falsos resets | Timeouts "
        "| Letras mal leídas | Tiempo medio (s) | Mediana (s) |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    rows = list(groups.items())
    if len(rows) > 1:
        rows.append(("**Total**", [s for ss in groups.values() for s in ss]))
    pairs = Counter()
    for name, sessions in rows:
        r = summarise(sessions)
        if not name.startswith("**"):
            pairs += r["misread_pairs"]
        lines.append(
            f"| {name or '(sin etiqueta)'} | {r['sessions']} | {r['attempts']} | {r['unlocked']} "
            f"| {_fmt(r['rate'], '{:.0%}')} | {r['false_resets']} | {r['timeouts']} "
            f"| {r['misread']} | {_fmt(r['time_mean'], '{:.1f}')} "
            f"| {_fmt(r['time_median'], '{:.1f}')} |")
    if pairs:
        lines += ["", "Letras mal leídas (esperada -> leída):", ""]
        lines += [f"- {pair}: {n}" for pair, n in pairs.most_common()]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Step 11 results table")
    parser.add_argument("logs", nargs="*", help="session CSVs (default: all in pasos/lse/pruebas)")
    parser.add_argument("--code", default="".join(config.UNLOCK_SEQUENCE))
    parser.add_argument("--out", help="also write the table to this .md file")
    args = parser.parse_args()

    paths = sorted(args.logs or glob.glob(os.path.join(LOG_DIR, "sesion_*.csv")))
    if not paths:
        raise SystemExit(f"No session logs in {LOG_DIR}: run python main.py --trials --log")
    groups: Dict[str, List[Session]] = {}
    for path in paths:
        session = parse_session(path, code=tuple(args.code.upper()))
        groups.setdefault(session.tag, []).append(session)
    table = markdown_table(groups)
    print(table)
    if args.out:
        with open(args.out, "w") as f:
            f.write(table)
        print(f"Saved in {args.out}")


if __name__ == "__main__":
    main()
