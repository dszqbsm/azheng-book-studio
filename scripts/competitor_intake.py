"""Inventory round-two research inputs without rewriting source material."""
import argparse
import csv
import json
import math
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1] / "references/competitor-research-68"
IDS = tuple(f"V{number:03d}" for number in range(1, 69))
COUNTS = ("views", "likes", "favorites", "shares", "comments", "follower_count_at_capture")
FIELDS = (
    "video_id", "book_id", "title", "book_title", "author", "book_category",
    "published_at", "captured_at", "duration_seconds", *COUNTS,
    "member_only", "pinned", "collection", "product_link", "cover_file",
    "transcript_file", "comments_file", "video_url", "notes",
)
FILES = {
    "transcript_file": ("transcripts", ".md"),
    "cover_file": ("covers", ".jpg"),
    "comments_file": ("comments", ".csv"),
}


def inventory(root):
    raw = root / "raw"
    errors, warnings = [], []
    rows, urls = {}, {}
    metadata = raw / "metadata.csv"
    try:
        with metadata.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle, strict=True)
            header = reader.fieldnames or []
            if not set(FIELDS) <= set(header) or len(header) != len(set(header)):
                errors.append("metadata.csv: missing required or duplicate columns")
            else:
                for row in reader:
                    if None in row or None in row.values():
                        errors.append(f"metadata.csv:{reader.line_num}: wrong number of columns")
                        continue
                    row = {key: value.strip() for key, value in row.items()}
                    video = row["video_id"]
                    if video not in IDS or video in rows:
                        errors.append(f"metadata.csv:{reader.line_num}: invalid or duplicate ID {video!r}")
                        continue
                    rows[video] = row
    except FileNotFoundError:
        warnings.append("metadata.csv not found")
    except (OSError, UnicodeError, csv.Error) as exc:
        errors.append(f"metadata.csv: {exc}")

    for video, row in rows.items():
        for field in COUNTS:
            if row[field] and not re.fullmatch(r"[0-9]+", row[field]):
                errors.append(f"{video}: {field} must be a nonnegative integer")
        if row["duration_seconds"]:
            try:
                duration = float(row["duration_seconds"])
                if not math.isfinite(duration) or duration <= 0:
                    raise ValueError
            except ValueError:
                errors.append(f"{video}: duration_seconds must be positive and finite")
        for field in ("member_only", "pinned"):
            if row[field] not in ("", "true", "false"):
                errors.append(f"{video}: {field} must be true, false or blank")
        if row["book_id"] and not re.fullmatch(r"B[0-9]{3,}", row["book_id"]):
            errors.append(f"{video}: invalid book_id")
        dates = {}
        for field in ("published_at", "captured_at"):
            if row[field]:
                try:
                    date = datetime.fromisoformat(row[field])
                    if date.utcoffset() is None:
                        raise ValueError
                    dates[field] = date
                except ValueError:
                    errors.append(f"{video}: {field} requires an ISO 8601 timestamp with offset")
        if len(dates) == 2 and dates["captured_at"] < dates["published_at"]:
            errors.append(f"{video}: capture precedes publication")
        if any(row[field] for field in COUNTS) and not row["captured_at"]:
            warnings.append(f"{video}: metrics lack a capture timestamp")
        for field in ("video_url", "product_link"):
            if not row[field]:
                continue
            try:
                url = urlsplit(row[field])
                if url.scheme not in ("http", "https") or not url.hostname:
                    raise ValueError
            except ValueError:
                errors.append(f"{video}: invalid {field}")
        if row["video_url"]:
            previous = urls.setdefault(row["video_url"], video)
            if previous != video:
                errors.append(f"{video}: duplicate video_url with {previous}")

    assets = {}
    for field, (folder, suffix) in FILES.items():
        received, missing = [], []
        names = {f"{video}{suffix}" for video in IDS}
        for path in sorted((raw / folder).glob("*")):
            if path.name not in names:
                warnings.append(f"Unexpected asset: {folder}/{path.name}")
        for video in IDS:
            name = f"{video}{suffix}"
            relative = f"{folder}/{name}"
            path = raw / relative
            declared = rows.get(video, {}).get(field, "")
            if declared and declared not in (name, relative):
                errors.append(f"{video}: {field} must match {relative}")
            if path.is_file() and path.stat().st_size:
                received.append(relative)
            else:
                missing.append(relative)
                if declared:
                    errors.append(f"{video}: declared asset missing or empty: {relative}")
        assets[folder] = {"received": received, "missing": missing}

    populated = [
        video for video in IDS if video in rows
        and any(value for key, value in rows[video].items() if key != "video_id")
    ]
    return {
        "expected_videos": len(IDS),
        "metadata_rows": len(rows),
        "populated_metadata": populated,
        "missing_metadata": [video for video in IDS if video not in populated],
        "assets": assets,
        "errors": errors,
        "warnings": warnings,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, help="New JSON inventory path; stdout by default.")
    args = parser.parse_args()
    report = inventory(args.root)
    result = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        with args.output.open("x", encoding="utf-8") as handle:
            handle.write(result)
    else:
        print(result, end="")
    return bool(report["errors"])


if __name__ == "__main__":
    raise SystemExit(main())
