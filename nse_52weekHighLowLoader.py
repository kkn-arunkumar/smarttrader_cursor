#!/usr/bin/env python3
"""Simple script to download NSE 52-week high/low CSV.
Default URL: https://archives.nseindia.com/content/CM_52_wk_High_low_06052026.csv
"""

import argparse
import os
import sys
try:
    from urllib.request import Request, urlopen
except Exception:
    # Python 2 fallback (unlikely on modern systems)
    from urllib2 import Request, urlopen  # type: ignore


def download_csv(url, out_path, chunk_size=8192):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    req = Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    })
    with urlopen(req) as resp:
        if resp.status and resp.status >= 400:
            raise RuntimeError(f"HTTP error {resp.status} when fetching {url}")
        with open(out_path, 'wb') as out_file:
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                out_file.write(chunk)
    return out_path


def main():
    parser = argparse.ArgumentParser(description='Download NSE 52-week High/Low CSV')
    parser.add_argument('--url', '-u', default='https://archives.nseindia.com/content/CM_52_wk_High_low_06052026.csv',
                        help='Full URL to CSV (default uses NSE archives sample file)')
    parser.add_argument('--out', '-o', default=os.path.join('downloads', os.path.basename('CM_52_wk_High_low_06052026.csv')),
                        help='Output file path (default: downloads/<filename>)')
    args = parser.parse_args()

    print(f"Downloading from: {args.url}")
    try:
        saved = download_csv(args.url, args.out)
        print(f"Saved to: {saved}")
    except Exception as e:
        print(f"Failed to download: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
