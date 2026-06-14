# NSE India to Oracle Loader

Python application to **download files from [NSE India](https://www.nseindia.com)** (e.g. equity bhav copy) and **load them into an Oracle database**.

## Features

- Download NSE equity **bhav copy** (EOD) ZIP from NSE archives; extracts CSV.
- Uses a session and proper headers (User-Agent, Referer) so NSE accepts the request.
- Tries multiple NSE URL patterns for reliability.
- Load CSV into Oracle with **batch insert** using **python-oracledb**.
- Optional: replace existing rows for the same date before insert.

## Requirements

- Python 3.9+
- Oracle Database (local or remote)
- Network access to `www.nseindia.com` / `nsearchives.nseindia.com`

## Setup

1. **Clone or copy the project** and create a virtual environment:

   ```bash
   cd SmartTrader_Cursor
   python -m venv .venv
   .venv\Scripts\activate    # Windows
   # source .venv/bin/activate   # Linux/macOS
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Oracle and optional settings:**

   - Copy `.env.example` to `.env`.
   - Set Oracle credentials and DSN in `.env`:

   ```env
   ORACLE_USER=your_username
   ORACLE_PASSWORD=your_password
   ORACLE_DSN=localhost:1521/ORCL
   ```

   For a TNS-style DSN:

   ```env
   ORACLE_DSN=(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=yourhost)(PORT=1521))(CONNECT_DATA=(SERVICE_NAME=ORCL)))
   ```

4. **Create the Oracle table** (optional; the app can create it automatically):

   ```bash
   sqlplus user/pass@dsn @scripts/create_nse_bhav_copy_table.sql
   ```

## Usage

- **Download latest bhav copy and load to Oracle:**

  ```bash
  python load_main.py
  ```

- **Specific date (YYYY-MM-DD):**

  ```bash
  python load_main.py --date 2025-03-07
  ```

- **Only download (no Oracle load):**

  ```bash
  python load_main.py --download-only
  ```

- **Only load an existing CSV:**

  ```bash
  python load_main.py --load-only downloads/cm07MAR2025bhav.csv
  ```

- **Replace existing data for that date before insert:**

  ```bash
  python load_main.py --date 2025-03-07 --replace
  ```

## Project layout

| File / folder            | Purpose |
|--------------------------|--------|
| `config.py`              | Loads `.env`; Oracle DSN, user, password, download dir, NSE headers |
| `nse_downloader.py`      | Download bhav copy (ZIP) from NSE, extract CSV |
| `oracle_loader.py`       | Create table, load bhav copy CSV into Oracle (batch insert) |
| `main.py`                | CLI: download and/or load |
| `scripts/create_nse_bhav_copy_table.sql` | Optional manual table creation |
| `.env.example`            | Template for `.env` (copy to `.env`) |
| `requirements.txt`       | Python dependencies |

## Extending to other NSE files

- **Other URLs:** Use `nse_downloader.download_file(url, output_path=...)` for any NSE file URL.
- **Other CSVs:** Use `oracle_loader.load_csv_to_oracle(csv_path, table_name, columns=[...])` and create the target table in Oracle as needed.

## Notes

- NSE provides data for **trading days**; avoid weekends and holidays for bhav copy.
- If download fails, NSE may have changed the URL or require different headers; check `nse_downloader.py` and update URLs/headers.
- Keep `.env` out of version control (add `.env` to `.gitignore`).
