# l10n-qa

QA for localized game/app strings: placeholders, length, encoding. A [Hermes](https://github.com/NousResearch/hermes-agent) skill.

Compares a source string file against its translation and flags the defects
that break builds or UI at runtime — before they ship.

## Install

Copy to your Hermes skills dir:

```bash
cp -r l10n-qa ~/.hermes/skills/software-development/
```

## Usage

```bash
python3 scripts/qa.py --src en/strings.properties --tgt id/strings.properties \
    [--format properties|xml|json] [--max-ratio 1.5]
```

Formats: Java `.properties`, Android `strings.xml`, flat JSON.

## Checks

| ID | Level | What |
|----|-------|------|
| P1 | FAIL | Placeholder mismatch (`%s`, `%d`, `%1$s`, `{0}`, `{name}`) — missing, extra, or reordered |
| P2 | WARN | Translation much longer than source (UI overflow risk) |
| P3 | WARN | String identical to source (untranslated?) |
| P4 | FAIL | Empty translation |
| P5 | FAIL | File is not valid UTF-8 |

Exit codes: `0` clean, `1` warnings only, `2` failures.

## Example

```bash
$ python3 scripts/qa.py --src en.properties --tgt id.properties
{
  "strings": 120,
  "checked": 118,
  "issues": [
    {"id": "P1", "level": "FAIL", "key": "welcome_msg",
     "detail": "placeholder mismatch: src=['{player}'] tgt=[]"}
  ],
  "verdict": "FAIL"
}
```

## Workflow

```
translate  →  l10n-qa  →  fix flagged strings  →  l10n-qa (re-verify)  →  ship
```

## License

MIT
