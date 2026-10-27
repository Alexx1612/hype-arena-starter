import csv
import json
import os
import re
import sys

MAX_BYTES = 16 * 1024 * 1024
CLAIMS = 1000
TYPES = {"fact", "compare", "change", "at_event", "relation"}
ID = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")


def read(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        data = f.read()
    first = data.split("\n", 1)[0]
    delimiter = ";" if first.count(";") > first.count(",") else ","
    return [{(k or "").strip().lower(): v for k, v in r.items()} for r in csv.DictReader(data.splitlines(), delimiter=delimiter)]


def number(s):
    try:
        return float((s or "").replace(",", ".", 1))
    except ValueError:
        return None


COLUMNS = {"id", "type", "text", "form", "label", "confidence"}


def check_labels(rows, practice, universe, problems):
    truth = {r["id"]: r["label"] for r in read(practice)}
    blank = [r["id"] for r in read(universe) if not r["label"]]
    seen, right, wrong, unsure = set(), 0, 0, 0
    for n, r in rows:
        rid, label = (r.get("id") or "").strip(), (r.get("label") or "").strip().lower()
        if rid in seen or rid not in blank:
            continue
        seen.add(rid)
        if label == "unsure":
            unsure += 1
            continue
        c = number(r.get("confidence"))
        if label not in ("true", "false") or c is None or not 0.5 <= c <= 1:
            problems.append(f"output.csv line {n}: label {label!r}, confidence {r.get('confidence')!r}")
            continue
        if truth.get(rid) in ("true", "false"):
            right, wrong = right + (label == truth[rid]), wrong + (label != truth[rid])
    print(f"labels: {len(seen)} of the {len(blank)} hidden rows labelled; "
          f"{right} right, {wrong} wrong, {unsure} unsure, against the practice labels")


def check_claims(rows, practice, problems):
    texts = {" ".join(r["text"].lower().split()).rstrip(".!? ") for r in read(practice)}
    ids = set()
    for n, r in rows[:CLAIMS]:
        why = []
        if not ID.match((r.get("id") or "").strip()) or r["id"] in ids:
            why.append("id")
        ids.add(r.get("id"))
        if r.get("type") not in TYPES:
            why.append("type")
        text = (r.get("text") or "").strip()
        if not text or len(text) > 300:
            why.append("text")
        if " ".join(text.lower().split()).rstrip(".!? ") in texts:
            why.append("a copy of an input row")
        try:
            if not isinstance(json.loads(r.get("form") or ""), dict):
                why.append("form")
        except ValueError:
            why.append("form")
        if (r.get("label") or "true").strip().lower() != "true":
            why.append("label not true")
        c = number(r.get("confidence"))
        if c is None or not 0.5 <= c <= 1:
            why.append("confidence")
        if why:
            problems.append(f"output.csv line {n}: {', '.join(why)}")
    if len(rows) != CLAIMS:
        problems.append(f"output.csv holds {len(rows)} new claims, not exactly {CLAIMS}"
                        + (f"; only the first {CLAIMS} are judged" if len(rows) > CLAIMS else ""))
    print(f"claims: {len(rows)} new claims")


def main(output, practice, universe):
    problems = []
    table = os.path.join(output, "output.csv")
    if os.path.islink(table) or (os.path.exists(table) and not os.path.isfile(table)):
        print("output.csv is not a regular file")
        return 1
    if not os.path.isfile(table):
        print("no table: the run did not write /output/output.csv")
        return 1
    if os.path.getsize(table) > MAX_BYTES:
        problems.append("output.csv is over 16 MiB")
    rows = read(table)
    columns = set(rows[0]) if rows else set()
    if rows and columns != COLUMNS:
        problems.append(f"output.csv: the columns are {sorted(columns)}, not {sorted(COLUMNS)}")
    else:
        numbered = list(enumerate(rows, start=2))
        check_labels([(n, r) for n, r in numbered if not (r.get("type") or "").strip()], practice, universe, problems)
        check_claims([(n, r) for n, r in numbered if (r.get("type") or "").strip()], practice, problems)
    for p in problems[:30]:
        print("  " + p)
    if len(problems) > 30:
        print(f"  and {len(problems) - 30} more")
    print("the format checks pass" if not problems else f"{len(problems)} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:4]))
