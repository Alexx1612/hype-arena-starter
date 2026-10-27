import csv
import sys


def main(practice, universe, every=5):
    with open(practice, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    hidden = 0
    with open(universe, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "text", "date", "label"])
        for i, r in enumerate(rows):
            label = r["label"]
            if i % every == 0:
                label = ""
                hidden += 1
            w.writerow([r["id"], r["text"], r["date"], label])
    print(f"input: {len(rows)} rows, {hidden} of them with the label hidden")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
