#!/usr/bin/env python3
"""Детерміновані перевірки humanizer-uk без моделі й залежностей.

    python evals/run_evals.py                      # перевірити еталонні правки з evals.json
    python evals/run_evals.py --outputs out.json   # перевірити виходи моделі {"id кейсу": "текст"}

Код виходу 0, якщо всі перевірки пройшли.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NBSP = " "
INVISIBLE = "­​‌⁠﻿"  # U+200D і U+FE0F лишаються: вони складають емодзі
NBSP_CHANNELS = {"site", "print", "doc"}
MONTHS = "січня|лютого|березня|квітня|травня|червня|липня|серпня|вересня|жовтня|листопада|грудня"
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⭐✅❗]")
NO_EMOJI_CHANNELS = {"email", "doc"}
PLAIN_CHANNELS = {"email", "chat", "social"}  # маркдаун там не відображається
UNIT = (r"(?:грн|zł|км|кг|хв|год|см|мм|ГБ|МБ|ТБ|день|дні|днів|тиждень|тижні|тижнів|місяць|місяці|місяців"
        rf"|рік|роки|років|р\.|{MONTHS})(?![\w’ʼ])")
CYR = "а-щьюяєіїґА-ЩЬЮЯЄІЇҐ"


def numbers(text: str) -> list[str]:
    """Числа без провідних нулів; «00» у «18:00» і самотній 0 не є фактом."""
    return sorted(n.lstrip("0") for n in re.findall(r"\d+", text) if n.lstrip("0"))


def paragraphs(text: str) -> list[str]:
    return [line for line in text.splitlines() if line.strip()]


def check(case: dict, out: str, banned: list[str]) -> dict[str, str | None]:
    """Повертає {назва перевірки: None, якщо пройшла, або опис проблеми}."""
    inp = case["input"]
    low = out.lower()
    r: dict[str, str | None] = {}

    if case.get("unchanged"):
        r["unchanged"] = None if out == inp else "текст мав лишитися без змін"
    else:
        r["not_longer"] = None if len(out) <= len(inp) else f"довший за вхід ({len(out)} > {len(inp)})"

    r["numbers_kept"] = None if numbers(out) == numbers(inp) else (
        f"числа змінилися: було {numbers(inp)}, стало {numbers(out)}")

    plain = out.replace(NBSP, " ")  # нерозривний пробіл не робить фрагмент іншим
    lost = [s for s in case.get("must_keep", []) if s not in plain]
    r["must_keep"] = None if not lost else f"втрачено: {lost}"

    if case.get("must_keep_any"):  # заклик можна переписати, але хоч один варіант має лишитися
        gone = [g for g in case["must_keep_any"] if not any(a.lower() in plain.lower() for a in g)]
        r["must_keep_any"] = None if not gone else f"немає жодного з: {gone}"

    found = [s for s in case.get("must_not_contain", []) if s in plain]  # з урахуванням регістру
    r["must_not_contain"] = None if not found else f"лишилося: {found}"

    hits = [b for b in banned if b in low]
    r["no_banned"] = None if not hits else f"заборонені звороти: {hits}"

    bad_letters = sorted(set(re.findall(r"[ыэъёЫЭЪЁ]", out)))
    mixed = re.findall(rf"\b\w*(?:[{CYR}][a-zA-Z]|[a-zA-Z][{CYR}])\w*\b", out)
    r["letters"] = None if not (bad_letters or mixed) else f"чужі літери: {bad_letters} {mixed}"

    quote_problems = []
    if '"' in out:
        quote_problems.append("прямі лапки")
    if "”" in out or out.count("„") != out.count("“"):
        quote_problems.append("англійські лапки замість «…» чи „…“")
    r["quotes"] = None if not quote_problems else ", ".join(quote_problems)

    apostrophe_problems = []
    if re.search(rf"[{CYR}]['`][{CYR}]", out):
        apostrophe_problems.append("прямий апостроф")
    if "’" in out and "ʼ" in out:
        apostrophe_problems.append("два види апострофа")
    r["apostrophe"] = None if not apostrophe_problems else ", ".join(apostrophe_problems)

    dash_problems = []
    if case.get("register") != "fiction":
        for p in paragraphs(out):
            if p.count("—") > 1:
                dash_problems.append(f"{p.count(chr(0x2014))} тире в абзаці «{p[:40]}…»")
    if re.search(r" (?:-|--|–) ", out):
        dash_problems.append("дефіс або коротке тире з пробілами на місці тире")
    r["dashes"] = None if not dash_problems else "; ".join(dash_problems)

    nbsp_problems = []
    if case.get("channel") in NBSP_CHANNELS:
        missing = re.findall(rf"\d+ {UNIT}", out)
        if missing:
            nbsp_problems.append(f"бракує нерозривного пробілу: {missing}")
    elif NBSP in out:
        nbsp_problems.append(f"нерозривний пробіл у каналі «{case.get('channel')}»")
    if any(ch in out for ch in INVISIBLE):
        nbsp_problems.append("невидимі символи")
    r["spaces"] = None if not nbsp_problems else "; ".join(nbsp_problems)

    markup = []
    if case.get("channel") in PLAIN_CHANNELS and "**" in out:
        markup.append(f"жирний **…** у каналі «{case.get('channel')}»")
    if case.get("channel") in PLAIN_CHANNELS and re.search(r"(?m)^#{1,6}\s", out):
        markup.append(f"маркдаун-заголовок у каналі «{case.get('channel')}»")
    if case.get("channel") in NO_EMOJI_CHANNELS and EMOJI.search(out):
        markup.append(f"емодзі в каналі «{case.get('channel')}»")
    r["markup"] = None if not markup else ", ".join(markup)
    return r


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--outputs", type=Path, help="JSON {\"id кейсу\": \"вихід моделі\"}")
    args = ap.parse_args()

    cfg = json.loads((HERE / "evals.json").read_text(encoding="utf-8"))
    banned = [b.lower() for b in cfg["banned"]]
    outputs = None
    if args.outputs:
        try:
            outputs = json.loads(args.outputs.read_text(encoding="utf-8-sig"))
        except UnicodeDecodeError:
            print(f"[помилка] {args.outputs} не в UTF-8; збережіть файл у UTF-8", file=sys.stderr)
            return 2
        except (OSError, json.JSONDecodeError) as exc:
            print(f"[помилка] не можу прочитати {args.outputs}: {exc}", file=sys.stderr)
            return 2

    failed = 0
    for case in cfg["cases"]:
        cid = case["id"]
        if outputs is not None:
            if cid not in outputs:
                print(f"SKIP  {cid}: немає виходу")
                continue
            out = outputs[cid]
        else:
            out = case["output"]
        results = check(case, out, banned)
        if outputs is None and not case.get("unchanged"):
            # Еталон має сенс, лише якщо у вході справді є що правити.
            tells = check(case, case["input"], banned)
            results["input_has_tells"] = None if any(
                tells[k] for k in ("no_banned", "dashes", "spaces", "quotes", "letters", "must_not_contain", "markup")
            ) else "у вході не знайдено жодного маркера"
        bad = {k: v for k, v in results.items() if v}
        status = "PASS" if not bad else "FAIL"
        print(f"{status}  {cid} [{case['register']}, {case['channel']}], перевірок: {len(results)}")
        for k, v in bad.items():
            print(f"      {k}: {v}")
        failed += bool(bad)

    total = len(cfg["cases"])
    print(f"\n{total - failed} з {total} кейсів пройшли")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
