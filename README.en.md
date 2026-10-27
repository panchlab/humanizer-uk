# humanizer-uk: Ukrainian text editing for AI agents

> Removes AI-writing tells from Ukrainian (uk, ua) text without changing what it says: stock AI phrases, Russianisms, Polish and English calques, bureaucratese, passive voice, chat markup and typography. Register-aware: a social post, a business email, a help page, an academic or legal text are each edited differently. Installs with one command into any agent that supports skills: Claude Code, Codex, Cursor, GitHub Copilot, Cline, Gemini CLI, Windsurf, OpenCode and 70+ more ([list](https://github.com/vercel-labs/skills/blob/main/docs/agents.md)).

> [Українська версія](README.md)

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.5.0-blueviolet)](CHANGELOG.md)
[![Stars](https://img.shields.io/github/stars/panchlab/humanizer-uk?style=social)](https://github.com/panchlab/humanizer-uk/stargazers)
[![skills.sh](https://skills.sh/b/panchlab/humanizer-uk)](https://skills.sh/panchlab/humanizer-uk/humanizer-uk)

**Before:**

> Шановний пане Олег! Надсилаю вам приведений нижче перелік документів по питанню оренди. В даний час договір підписується директором, тому прошу підтвердити отримання на протязі тижня.

**After:**

> Шановний пане Олеже! Надсилаю вам наведений нижче перелік документів щодо оренди. Зараз договір підписує директор, тому прошу підтвердити отримання протягом тижня.

Five edits in a business email: the vocative case, two Russianisms («приведений», «на протязі»), two bureaucratic connectors («по питанню», «в даний час») and a passive turned active. The content, the deadline and the tone are unchanged, nothing was added. Across 28 test texts the skill changed no numbers, kept emoji and bold headings where they are part of the format, and in 6 human-written samples corrected a single stray character ([details](#evaluation)).

It edits for people, not for detectors. GPTZero, Copyleaks and similar tools may still flag the result: the skill does not try to get past them, and we do not test for it.

## Install

One command for any of 80 agents; the CLI finds the installed ones and asks where to put it. No other skill is required:

```bash
npx skills add panchlab/humanizer-uk
```

In Claude Code you can install it as a plugin, so updates arrive through `/plugin`:

```text
/plugin marketplace add panchlab/humanizer-uk
/plugin install humanizer-uk@humanizer-uk
```

Claude.ai and Claude Desktop: download the repository as ZIP and add it as a skill in settings.

## Usage

- "Humanize this", "proofread the style": edit mode, returns the corrected text.
- "What gives away AI here?": audit mode, a list of markers without rewriting.
- "Only remove the bureaucratese", "fix the quotes": targeted edit.
- Paste your own texts as a voice sample: replacements follow your rhythm and punctuation.

## What it fixes

- **General AI patterns** ([§1–§26](references/patterns.md), in Ukrainian): not-X-but-Y, dramatic fragments, forced triads, dashes everywhere, inflated significance, bold as decoration, chatbot residue.
- **AI phrasing:** «зануртеся у світ…», «не просто…, а…», «відіграє ключову роль»; in posts, newsletters and press releases also the soft marketing filler («найкращі ціни сезону», «ідеальне місце для…»).
- **Chat markup:** bold, markdown headings, emoji and template lines are removed only where the channel cannot render them; page, help-article and post structure stays.
- **Russianisms:** «приймати участь», «на протязі», «задача» meaning "task", active participles in -учий/-ючий.
- **Polish calques:** «забронювати візит», «під адресою», «в годинах 9–17». Built for Ukrainians in Poland and for translations from Polish.
- **English calques:** «на щоденній основі», «адресувати проблему», «реальний вплив», Title Case in headings.
- **Bureaucratese and passive voice:** «здійснюємо доставку», «з метою», «лист підписується директором».
- **Typography:** «…» quotes, the ’ apostrophe, dashes per the 2019 orthography, non-breaking spaces for web and print, Latin or Cyrillic look-alike letters inside Ukrainian words.

Register matters: academic passive voice stays, legal text gets only obvious fixes, business-letter courtesy formulas and fiction dialogue are left alone.

## What it does not do

- Add facts, numbers, names or details "for liveliness".
- Cut function along with filler: calls to action, offers, deadlines, prices and contacts stay.
- Translate; translation happens separately, the skill proofreads the result.
- Touch human-written text unasked: if the text is yours, only clear errors are fixed.
- Evade AI detectors, insert typos or invisible characters.

## Evaluation

Deterministic checks with no model and no dependencies, Python 3.9+ only:

```bash
python evals/run_evals.py
```

The runner checks the [reference edits](evals/evals.json): numbers and required fragments kept, no Russian letters, straight quotes or apostrophes, no dashes over the limit, no markup outside its channel, no banned phrases. Pass model outputs with `--outputs`.

Blind test (October 2026): 28 texts in 13 genres (18 generated by four Claude models, 10 from the evals), eight systems run on the same model, two model judges (Claude and GPT), versions in random order. Version 1.3 ranked first of eight summed over both judges and lost facts least often: 5–6 texts versus 13–14 for the bare model; the gap to the nearest competitors is within noise, the gain over the bare model is significant. Results for 1.4 will be added after its run. This is a small-sample, model-judged result, not a quality guarantee for every text.

## References

Rules and examples are original; no dictionary entries were copied. For disputed cases see the [Ukrainian orthography 2019](https://mon.gov.ua/static-objects/mon/sites/1/zagalna%20serednya/Pravopys.2019/ukr.pravopys-2019.pdf), B. Antonenko-Davydovych "Як ми говоримо", O. Ponomariv "Культура слова", S. Karavansky's dictionary of difficult vocabulary and the [Ukrainian rules in LanguageTool](https://github.com/languagetool-org/languagetool/tree/master/languagetool-language-modules/uk/src/main/resources/org/languagetool/rules/uk) (LGPL 2.1).

## License

[MIT](LICENSE). The general patterns §1–§26 in [references/patterns.md](references/patterns.md) were written from scratch after the ideas and numbering of [blader/humanizer](https://github.com/blader/humanizer) (MIT, © 2025 Siqi Chen); its text is not copied. Changes are listed in [CHANGELOG.md](CHANGELOG.md).
