"""
NSE India → Oracle: download bhav copy (and other) files from NSE and load into Oracle.
Usage:
  python main.py                    # download latest bhav copy and load to Oracle
  python main.py --date 2025-03-07  # specific date (YYYY-MM-DD)
  python main.py --download-only    # only download, do not load
  python main.py --load-only <path> # only load from existing CSV
"""
import argparse
from datetime import datetime
from pathlib import Path

from config import DOWNLOAD_DIR
from nse_downloader import download_bhav_copy
from oracle_loader import load_bhav_copy_to_oracle


def main():
    parser = argparse.ArgumentParser(
        description="Download NSE India files and load into Oracle database."
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Date for bhav copy (YYYY-MM-DD). Default: previous trading day.",
    )
    parser.add_argument(
        "--download-dir",
        type=Path,
        default=DOWNLOAD_DIR,
        help="Directory to save downloaded files.",
    )
    parser.add_argument(
        "--download-only",
        action="store_true",
        help="Only download; do not load to Oracle.",
    )
    parser.add_argument(
        "--load-only",
        type=Path,
        metavar="CSV_PATH",
        default=None,
        help="Only load this CSV file to Oracle (skip download).",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Delete existing rows for the same date before insert (upsert by date).",
    )
    args = parser.parse_args()

    if args.load_only:
        csv_path = Path(args.load_only)
        if not csv_path.exists():
            print(f"File not found: {csv_path}")
            return 1
        print(f"Loading {csv_path} into Oracle...")
        n = load_bhav_copy_to_oracle(csv_path, create_table=True)
        print(f"Inserted {n} rows.")
        return 0

    for_date = None
    if args.date:
        try:
            for_date = datetime.strptime(args.date, "%Y-%m-%d")
        except ValueError:
            print("Invalid --date. Use YYYY-MM-DD.")
            return 1

    print("Downloading NSE bhav copy...")
    csv_path = download_bhav_copy(for_date=for_date, output_dir=args.download_dir)
    if not csv_path or not csv_path.exists():
        print("Download failed. Check date (trading day) and network.")
        return 1
    print(f"Downloaded: {csv_path}")

    if args.download_only:
        return 0

    replace_for_date = None
    if args.replace and for_date:
        replace_for_date = for_date.strftime("%d-%b-%Y").upper()  # Oracle DD-MON-YYYY
    elif args.replace and csv_path.exists():
        # Try to infer date from filename, e.g. cm07MAR2025bhav.csv
        name = csv_path.stem
        if "bhav" in name.lower():
            replace_for_date = name.replace("cm", "").replace("bhav", "")  # e.g. 07MAR2025
            if len(replace_for_date) >= 9:
                replace_for_date = (replace_for_date[:2] + "-" + replace_for_date[2:5] + "-" + replace_for_date[5:]).upper()

    print("Loading into Oracle...")
    n = load_bhav_copy_to_oracle(
        csv_path,
        create_table=True,
        replace_for_date=replace_for_date,
    )
    print(f"Inserted {n} rows into NSE_BHAV_COPY.")
    return 0


if __name__ == "__main__":
    exit(main())
