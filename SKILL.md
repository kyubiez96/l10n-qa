---
name: l10n-qa
description: "QA localized strings: placeholders, length, encoding."
requires_toolsets: [file, terminal]
---

# L10n-QA

Quality gate for translated game/app strings — the missing layer in
KuroPatch's pipeline. Compares a source string file against its translation
and flags the defects that break builds or UI at runtime: placeholder
mismatches, length overflow, untranslated strings, empty values, encoding
problems.

## When to use

- After KuroPatch (or any translator) produces a translated string file.
- Kovak says "cek terjemahan", "qa l10n", or pastes a translated file.
- In CI for a localization repo: fail on FAIL, warn on WARN.

## How it works

```
python3 scripts/qa.py --src en/strings.properties --tgt id/strings.properties \
    [--format properties|xml|json] [--max-ratio 1.5]
```

Formats: Java `.properties` (`key=value`), Android `strings.xml`
(`<string name="k">v</string>`), flat JSON (`{"k":"v"}`).

## Checks

| ID | Level | What |
|----|-------|------|
| P1 | FAIL | Placeholder mismatch: `%s`/`%d`/`%1$s`/`{0}`/`{name}` present in source but missing, extra, or reordered in translation |
| P2 | WARN | Length ratio `len(tgt)/len(src)` > `--max-ratio` (default 1.5) — UI overflow risk |
| P3 | WARN | Untranslated: tgt identical to src (skipped when src is non-translatable: numbers, URLs, symbols) |
| P4 | FAIL | Empty translation value |
| P5 | FAIL | File is not valid UTF-8 |

Output: one JSON report to stdout. Exit 0 = clean, 1 = warnings only,
2 = failures present.

```json
{
  "src": "en.properties", "tgt": "id.properties",
  "strings": 120, "checked": 118,
  "issues": [
    {"id": "P1", "level": "FAIL", "key": "welcome_msg",
     "detail": "placeholder {player} in src missing in tgt",
     "src": "Welcome, {player}!", "tgt": "Selamat datang!"}
  ],
  "verdict": "PASS|WARN|FAIL"
}
```

## Workflow with KuroPatch

```
KuroPatch translate  →  l10n-qa  →  fix flagged strings  →  l10n-qa (re-verify)  →  ship
```

## Honest limits

- Placeholder detection covers printf-style (`%s`, `%d`, `%1$s`) and brace
  style (`{0}`, `{name}`). Custom engine syntaxes need the regex extended.
- Length ratio is a heuristic, not a layout engine. CJK scripts and narrow
  UI elements need manual review.
- P3 can't tell "intentionally kept in English" from "forgot to translate" —
  it flags, you decide.
- Checks *strings*, not context. A grammatically perfect translation of the
  wrong meaning still passes.
