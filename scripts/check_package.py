#!/usr/bin/env python3
"""Перевіряє файли пакета humanizer-uk без залежностей.

    python scripts/check_package.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE_PATTERNS = 26          # humanizer 3.1.0: §1–§26
NUMBERED_SECTIONS = 11      # надбудови посилаються на розділи 1–11 за номерами
DESCRIPTION_MAX = 1024      # Agent Skills specification
SKILL_MAX_LINES = 500


def read(rel: str) -> str:
    try:
        return (ROOT / rel).read_text(encoding="utf-8")
    except OSError as exc:
        sys.exit(f"Не можу прочитати {rel}: {exc}")


def main() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    problems: list[str] = []
    skill = read("SKILL.md")
    m = re.match(r"\A---\n(.*?)\n---\n", skill, re.DOTALL)
    if not m:
        sys.exit("SKILL.md має починатися з YAML-фронтматеру")
    meta = m.group(1)

    if not re.search(r"(?m)^name: humanizer-uk$", meta):
        problems.append("name у SKILL.md має бути humanizer-uk")
    if re.search(r"(?m)^(version|allowed-tools):", meta):
        problems.append("version тримати в metadata.version, не на верхньому рівні")
    desc_m = re.search(r"(?m)^description: \|\n((?:  .*\n)+)", meta + "\n")
    description = " ".join(desc_m.group(1).split()) if desc_m else ""
    if not description:
        problems.append("опис у SKILL.md має бути блоком «description: |»")
    elif len(description) > DESCRIPTION_MAX:
        problems.append(f"опис {len(description)} символів, ліміт {DESCRIPTION_MAX}")
    lines = skill.count("\n")
    if lines > SKILL_MAX_LINES:
        problems.append(f"SKILL.md {lines} рядків, рекомендовано до {SKILL_MAX_LINES}")

    ver_m = re.search(r'(?m)^\s+version:\s*"([0-9]+\.[0-9]+\.[0-9]+)"', meta)
    versions = {"SKILL.md": ver_m.group(1) if ver_m else "?"}
    plugin = json.loads(read(".claude-plugin/plugin.json"))
    market = json.loads(read(".claude-plugin/marketplace.json"))
    evals = json.loads(read("evals/evals.json"))
    versions["plugin.json"] = plugin.get("version", "?")
    versions["evals.json"] = evals.get("version", "?")
    ch_m = re.search(r"(?m)^## ([0-9]+\.[0-9]+\.[0-9]+)$", read("CHANGELOG.md"))
    versions["CHANGELOG.md"] = ch_m.group(1) if ch_m else "?"
    if len(set(versions.values())) != 1:
        problems.append(f"різні версії: {versions}")

    first_sentence = description.split(". ")[0].rstrip(".") + "."
    manifest_descriptions = {plugin.get("description")} | {
        p.get("description") for p in market.get("plugins", [])}
    if manifest_descriptions != {first_sentence}:
        problems.append(f"опис у маніфестах має бути першим реченням SKILL.md: «{first_sentence}»")
    if plugin.get("skills") != ["./"]:
        problems.append("plugin.json: skills має бути [\"./\"]")

    refs = sorted({int(n) for n in re.findall(r"§(\d+)", skill)})
    out_of_range = [n for n in refs if not 1 <= n <= BASE_PATTERNS]
    if out_of_range:
        problems.append(f"посилання на неіснуючі патерни базового скіла: {out_of_range}")
    numbered = [int(n) for n in re.findall(r"(?m)^## (\d+)\. ", skill)]
    if numbered != list(range(1, NUMBERED_SECTIONS + 1)):
        problems.append(f"розділи мають іти 1–{NUMBERED_SECTIONS} без пропусків: {numbered}")

    for rel in ("README.md", "CHANGELOG.md"):
        for link in re.findall(r"\]\(([^)#]+)(?:#[^)]*)?\)", read(rel)):
            if not link.startswith(("http://", "https://")) and not (ROOT / link).exists():
                problems.append(f"{rel}: битий локальний лінк {link}")

    if problems:
        print("Проблеми в пакеті:")
        for p in problems:
            print(f"  - {p}")
        sys.exit(1)
    print(f"Пакет humanizer-uk v{versions['SKILL.md']} у порядку: "
          f"{lines} рядків, опис {len(description)} символів, §{refs[0]}–§{refs[-1]}")


if __name__ == "__main__":
    main()
