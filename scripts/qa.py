#!/usr/bin/env python3
"""l10n-qa: QA checks for localized string files.

Usage:
    python3 qa.py --src en.properties --tgt id.properties
                  [--format properties|xml|json] [--max-ratio 1.5]

Exit 0: PASS. 1: WARN only. 2: FAIL present.
"""
import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET

PLACEHOLDER_RE = re.compile(r"%\d*\$?[sdf]|{\d+}|{[a-zA-Z_][a-zA-Z0-9_]*}")
NON_TRANSLATABLE_RE = re.compile(r"^[\d\s\W]*$|^https?://", re.IGNORECASE)


def placeholders(s):
    return PLACEHOLDER_RE.findall(s or "")


def load_properties(path):
    out = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(("#", "!")):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
            elif ":" in line:
                k, v = line.split(":", 1)
            else:
                continue
            out[k.strip()] = v.strip()
    return out


def load_xml(path):
    out = {}
    tree = ET.parse(path)
    for s in tree.getroot().iter("string"):
        name = s.get("name")
        if name:
            out[name] = "".join(s.itertext()).strip()
    return out


def load_json(path):
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    return {str(k): str(v) for k, v in d.items()}


LOADERS = {"properties": load_properties, "xml": load_xml, "json": load_json}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--tgt", required=True)
    ap.add_argument("--format", default="properties", choices=list(LOADERS))
    ap.add_argument("--max-ratio", type=float, default=1.5)
    args = ap.parse_args()

    issues = []
    report = {"src": args.src, "tgt": args.tgt, "strings": 0,
              "checked": 0, "issues": issues, "verdict": "PASS"}

    def add(iid, level, key, detail, src_v="", tgt_v=""):
        issues.append({"id": iid, "level": level, "key": key,
                       "detail": detail, "src": src_v, "tgt": tgt_v})

    # P5: encoding — loaders already decode utf-8 strictly
    try:
        src_map = LOADERS[args.format](args.src)
    except UnicodeDecodeError:
        add("P5", "FAIL", "*", f"{args.src} is not valid UTF-8", "", "")
        print(json.dumps(report, indent=2))
        return 2
    except Exception as e:
        print(json.dumps({"verdict": "FAIL", "error": f"cannot parse src: {e}"}, indent=2))
        return 2
    try:
        tgt_map = LOADERS[args.format](args.tgt)
    except UnicodeDecodeError:
        add("P5", "FAIL", "*", f"{args.tgt} is not valid UTF-8", "", "")
        print(json.dumps(report, indent=2))
        return 2
    except Exception as e:
        print(json.dumps({"verdict": "FAIL", "error": f"cannot parse tgt: {e}"}, indent=2))
        return 2

    report["strings"] = len(tgt_map)
    for key, tgt_v in tgt_map.items():
        src_v = src_map.get(key)
        if src_v is None:
            continue  # extra key in tgt; not our problem here
        report["checked"] += 1

        # P4: empty
        if not tgt_v:
            add("P4", "FAIL", key, "empty translation", src_v, tgt_v)
            continue

        # P1: placeholders (multiset comparison — order matters for printf)
        sp, tp = placeholders(src_v), placeholders(tgt_v)
        if sorted(sp) != sorted(tp):
            add("P1", "FAIL", key,
                f"placeholder mismatch: src={sp} tgt={tp}", src_v, tgt_v)
        elif sp != tp and sp:
            add("P1", "FAIL", key,
                f"placeholder order changed: src={sp} tgt={tp}", src_v, tgt_v)

        # P2: length ratio
        if src_v and len(tgt_v) / max(len(src_v), 1) > args.max_ratio:
            add("P2", "WARN", key,
                f"length ratio {len(tgt_v)/len(src_v):.2f} > {args.max_ratio} (UI overflow risk)",
                src_v, tgt_v)

        # P3: untranslated
        if tgt_v == src_v and not NON_TRANSLATABLE_RE.match(src_v):
            add("P3", "WARN", key, "identical to source — untranslated?", src_v, tgt_v)

    levels = {i["level"] for i in issues}
    report["verdict"] = "FAIL" if "FAIL" in levels else ("WARN" if "WARN" in levels else "PASS")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return {"PASS": 0, "WARN": 1, "FAIL": 2}[report["verdict"]]


if __name__ == "__main__":
    sys.exit(main())
