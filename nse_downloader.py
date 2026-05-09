"""
Download bhav copy (and other) files from NSE India.
Uses a session and proper headers; tries multiple URL patterns.
"""
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests

from config import DOWNLOAD_DIR, NSE_HEADERS


def _nse_session() -> requests.Session:
    """Create a session and optionally prime cookies by visiting NSE homepage."""
    session = requests.Session()
    session.headers.update(NSE_HEADERS)
    try:
        session.get("https://www.nseindia.com", timeout=15)
    except requests.RequestException:
        pass
    return session


def _bhav_copy_urls(for_date: datetime) -> list[str]:
    """Return candidate URLs for NSE equity bhav copy (newest first)."""
    yyyy, mm, dd = for_date.year, for_date.month, for_date.day
    yyyymmdd = f"{yyyy}{mm:02d}{dd:02d}"
    month_abbr = for_date.strftime("%b").upper()
    day_pad = f"{dd:02d}"

    return [
        # NSE archives (current format)
        f"https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_{yyyymmdd}_F_0000.csv.zip",
        # Historical equities path
        f"https://www.nseindia.com/content/historical/EQUITIES/{yyyy}/{month_abbr}/cm{day_pad}{month_abbr}{yyyy}bhav.csv.zip",
        f"https://archives.nseindia.com/content/historical/EQUITIES/{yyyy}/{month_abbr}/cm{day_pad}{month_abbr}{yyyy}bhav.csv.zip",
    ]


def download_bhav_copy(
    for_date: Optional[datetime] = None,
    output_dir: Optional[Path] = None,
) -> Optional[Path]:
    """
    Download NSE equity bhav copy ZIP for the given date, extract CSV, return path to CSV.
    If for_date is None, uses the latest available (previous trading day).
    Returns path to the extracted CSV file, or None if download failed.
    """
    for_date = for_date or datetime.now()
    output_dir = output_dir or DOWNLOAD_DIR
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    urls = _bhav_copy_urls(for_date)
    ##print(url)
    session = _nse_session()

    zip_path = output_dir / f"cm_bhav_copy_{for_date.strftime('%Y%m%d')}.zip"
    csv_name = f"cm{for_date.strftime('%d%b%Y').upper()}bhav.csv"
    csv_path = output_dir / csv_name

    # If CSV already extracted, return it
    if csv_path.exists():
        return csv_path

    for url in urls:
        try:
            print(url)
            r = session.get(url, timeout=30, stream=True)
            r.raise_for_status()
            with open(zip_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            break
        except (requests.RequestException, OSError):
            continue
    else:
        return None

    extracted_path = None
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()
            if not names:
                return None
            first = names[0]
            zf.extract(first, path=output_dir)
            extracted_path = output_dir / first
    except (zipfile.BadZipFile, OSError):
        extracted_path = None
    finally:
        if zip_path.exists():
            zip_path.unlink(missing_ok=True)

    return extracted_path


def download_file(
    url: str,
    output_path: Optional[Path] = None,
    output_dir: Optional[Path] = None,
) -> Optional[Path]:
    """
    Download a single file from NSE (any URL). Uses NSE session headers.
    Either output_path or output_dir must be provided; if output_dir, filename from URL is used.
    """
    if output_path is None and output_dir is None:
        output_dir = DOWNLOAD_DIR
    if output_path is None:
        output_path = Path(output_dir) / url.split("/")[-1].split("?")[0]
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    session = _nse_session()
    try:
        r = session.get(url, timeout=60, stream=True)
        r.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        return output_path
    except (requests.RequestException, OSError):
        return None
