# paso 11: tabla de resultados a partir de los csv de las sesiones
#   python -m lse_auth.trial_report [csvs] [--out fichero.md]
#
# un intento empieza con la primera letra buena (o un restart) y acaba con
# unlocked, wrong, restart, timeout o reset (r, ese no cuenta).
# wrong/restart dentro de un intento = letra mal leida (esperada->leida).
# wrong sin intento abierto = letra suelta (seguramente la mano moviendose
# entre signos), va aparte. En la sesion de impostor son todas asi

import argparse
import csv
import glob
import os
import statistics
from collections import Counter
from dataclasses import dataclass, field

from lse_auth import config

LOG_DIR = os.path.join(config.PROJECT_ROOT, "pasos", "lse", "pruebas")


@dataclass
class Attempt:
    start: float
    end: float = None
    result: str = None

    @property
    def duration(self):
        return None if self.end is None else self.end - self.start


@dataclass
class Session:
    name: str
    tag: str
    attempts: list = field(default_factory=list)
    misread: Counter = field(default_factory=Counter)    # "O->H": n
    stray_wrong: int = 0                                 # letras sueltas

    def count(self, result):
        return sum(a.result == result for a in self.attempts)

    @property
    def finished(self):
        # sin los abortados con r ni los que se quedan abiertos
        return [a for a in self.attempts if a.result not in (None, "reset")]


def tag_of(path):
    # sesion_20261124_101500_natural.csv -> natural
    parts = os.path.splitext(os.path.basename(path))[0].split("_", 3)
    return parts[3] if len(parts) == 4 else ""


def parse_session(path, code=config.UNLOCK_SEQUENCE):
    session = Session(name=os.path.basename(path), tag=tag_of(path))
    current = None
    typed = 0

    def close(t, result):
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
                    session.stray_wrong += 1
                else:
                    session.misread[f"{expected}->{letter}"] += 1
                    close(t, "wrong")
            elif event in ("timeout", "reset"):
                close(t, event)
    return session


def summarise(sessions):
    finished = [a for s in sessions for a in s.finished]
    ok = [a for a in finished if a.result == "unlocked"]
    times = [a.duration for a in ok]
    bad = sum(s.count("wrong") + s.count("restart") for s in sessions)
    return {
        "sessions": len(sessions),
        "attempts": len(finished),
        "unlocked": len(ok),
        "rate": len(ok) / len(finished) if finished else None,
        "false_resets": bad,
        "timeouts": sum(s.count("timeout") for s in sessions),
        "misread": bad,
        "loose": sum(s.stray_wrong for s in sessions),
        "misread_pairs": sum((s.misread for s in sessions), Counter()),
        "time_mean": statistics.mean(times) if times else None,
        "time_median": statistics.median(times) if times else None,
    }


def _fmt(value, pattern):
    return "-" if value is None else pattern.format(value)


def markdown_table(groups):
    lines = [
        "| Condición | Sesiones | Intentos | Desbloqueos | Tasa | Falsos resets | Timeouts "
        "| Letras mal leídas | Letras sueltas | Tiempo medio (s) | Mediana (s) |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
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
            f"| {r['misread']} | {r['loose']} | {_fmt(r['time_mean'], '{:.1f}')} "
            f"| {_fmt(r['time_median'], '{:.1f}')} |")
    if pairs:
        lines += ["", "Letras mal leídas (esperada -> leída):", ""]
        lines += [f"- {pair}: {n}" for pair, n in pairs.most_common()]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Step 11 results table")
    parser.add_argument("logs", nargs="*", help="session CSVs (default: all in pasos/lse/pruebas)")
    parser.add_argument("--code", default="".join(config.UNLOCK_SEQUENCE))
    parser.add_argument("--out", help="also write the table to this .md file")
    args = parser.parse_args()

    paths = sorted(args.logs or glob.glob(os.path.join(LOG_DIR, "sesion_*.csv")))
    if not paths:
        raise SystemExit(f"No session logs in {LOG_DIR}: run python main.py --trials --log")
    groups = {}
    for path in paths:
        s = parse_session(path, code=tuple(args.code.upper()))
        groups.setdefault(s.tag, []).append(s)
    table = markdown_table(groups)
    print(table)
    if args.out:
        with open(args.out, "w") as f:
            f.write(table)
        print(f"Saved in {args.out}")


if __name__ == "__main__":
    main()
