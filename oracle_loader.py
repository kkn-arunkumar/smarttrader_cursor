"""
Load NSE bhav copy CSV (and similar) data into Oracle using python-oracledb.
Uses batch insert for efficiency.
"""
from pathlib import Path
from typing import Optional

import oracledb
import pandas as pd

from config import ORACLE_BATCH_SIZE, ORACLE_DSN, ORACLE_PASSWORD, ORACLE_USER


# Target CSV columns (from the NSE file) -> Oracle table columns
BHAV_COPY_COLUMNS = [
    "TradDt",
    "BizDt",
    "Sgmt",
    "Src",
    "FinInstrmTp",
    "FinInstrmId",
    "ISIN",
    "TckrSymb",
    "SctySrs",
    "XpryDt",
    "FininstrmActlXpryDt",
    "StrkPric",
    "OptnTp",
    "FinInstrmNm",
    "OpnPric",
    "HghPric",
    "LwPric",
    "ClsPric",
    "LastPric",
    "PrvsClsgPric",
    "UndrlygPric",
    "SttlmPric",
    "OpnIntrst",
    "ChngInOpnIntrst",
    "TtlTradgVol",
    "TtlTrfVal",
    "TtlNbOfTxsExctd",
    "SsnId",
    "NewBrdLotQty",
    "Rmks",
    "Rsvd1",
    "Rsvd2",
    "Rsvd3",
    "Rsvd4",
]



def get_connection():
    """Create and return an Oracle connection using config."""
    return oracledb.connect(
        user=ORACLE_USER,
        password=ORACLE_PASSWORD,
        dsn=ORACLE_DSN,
    )


def create_bhav_copy_table(cursor) -> None:
    """
    Create the NSE bhav copy table if it does not exist.
    Table: NSE_BHAV_COPY
    """
    ddl = (
        "CREATE TABLE NSE_BHAV_COPY ("
        "TradDt DATE, "
        "BizDt DATE, "
        "Sgmt VARCHAR2(10), "
        "Src VARCHAR2(10), "
        "FinInstrmTp VARCHAR2(20), "
        "FinInstrmId VARCHAR2(50), "
        "ISIN VARCHAR2(20), "
        "TckrSymb VARCHAR2(50), "
        "SctySrs VARCHAR2(20), "
        "XpryDt DATE, "
        "FininstrmActlXpryDt DATE, "
        "StrkPric NUMBER(20,4), "
        "OptnTp VARCHAR2(5), "
        "FinInstrmNm VARCHAR2(200), "
        "OpnPric NUMBER(20,4), "
        "HghPric NUMBER(20,4), "
        "LwPric NUMBER(20,4), "
        "ClsPric NUMBER(20,4), "
        "LastPric NUMBER(20,4), "
        "PrvsClsgPric NUMBER(20,4), "
        "UndrlygPric NUMBER(20,4), "
        "SttlmPric NUMBER(20,4), "
        "OpnIntrst NUMBER(20), "
        "ChngInOpnIntrst NUMBER(20), "
        "TtlTradgVol NUMBER(20), "
        "TtlTrfVal NUMBER(20,4), "
        "TtlNbOfTxsExctd NUMBER(20), "
        "SsnId VARCHAR2(10), "
        "NewBrdLotQty NUMBER(20), "
        "Rmks VARCHAR2(4000), "
        "Rsvd1 VARCHAR2(100), "
        "Rsvd2 VARCHAR2(100), "
        "Rsvd3 VARCHAR2(100), "
        "Rsvd4 VARCHAR2(100), "
        "LOAD_DATE DATE DEFAULT SYSDATE, "
        "PRIMARY KEY (TradDt, TckrSymb, SctySrs, XpryDt, StrkPric, OptnTp))"
    )
    try:
        cursor.execute(ddl)
    except oracledb.DatabaseError as e:
        if e.args[0].code != 955:  # name already used
            raise


def _parse_bhav_csv(csv_path: Path) -> pd.DataFrame:
    """Read NSE bhav copy CSV and normalize columns."""
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()
    available = [c for c in BHAV_COPY_COLUMNS if c in df.columns]
    df = df[available].copy()
    # Parse date columns
    for date_col in ("TradDt", "BizDt", "XpryDt", "FininstrmActlXpryDt"):
        if date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    # Numeric columns
    numeric_cols = [
        "StrkPric",
        "OpnPric",
        "HghPric",
        "LwPric",
        "ClsPric",
        "LastPric",
        "PrvsClsgPric",
        "UndrlygPric",
        "SttlmPric",
        "OpnIntrst",
        "ChngInOpnIntrst",
        "TtlTradgVol",
        "TtlTrfVal",
        "TtlNbOfTxsExctd",
        "NewBrdLotQty",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    # Require at least trade date and ticker
    required = [c for c in ("TradDt", "TckrSymb") if c in df.columns]
    return df.dropna(subset=required) if required else df


def load_bhav_copy_to_oracle(
    csv_path: Path,
    table_name: str = "NSE_BHAV_COPY",
    create_table: bool = True,
    replace_for_date: Optional[str] = None,
) -> int:
    """
    Load a bhav copy CSV file into Oracle.
    - create_table: if True, creates NSE_BHAV_COPY when missing.
    - replace_for_date: if set (e.g. '07-MAR-2025'), deletes existing rows for that TradDt before insert.
    Returns number of rows inserted.
    """
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    df = _parse_bhav_csv(csv_path)
    if df.empty:
        return 0

    conn = get_connection()
    try:
        cursor = conn.cursor()
        if create_table:
            create_bhav_copy_table(cursor)

        if replace_for_date:
            cursor.execute(
                "DELETE FROM NSE_BHAV_COPY WHERE TradDt = TO_DATE(:1,'DD-MON-YYYY')",
                [replace_for_date],
            )
            conn.commit()

        # Build INSERT matching the new NSE columns
        col_list = ",".join(BHAV_COPY_COLUMNS)
        placeholders = ",".join([f":{i+1}" for i in range(len(BHAV_COPY_COLUMNS))])
        insert_sql = f"INSERT INTO {table_name} ({col_list}) VALUES ({placeholders})"
        rows = df[BHAV_COPY_COLUMNS].to_numpy().tolist()
        # Convert NaT/NaN to None for Oracle
        for row in rows:
            for i, v in enumerate(row):
                if pd.isna(v):
                    row[i] = None

        total = 0
        for i in range(0, len(rows), ORACLE_BATCH_SIZE):
            batch = rows[i : i + ORACLE_BATCH_SIZE]
            cursor.executemany(insert_sql, batch)
            total += len(batch)
        conn.commit()
        return total
    finally:
        conn.close()


def load_csv_to_oracle(
    csv_path: Path,
    table_name: str,
    columns: Optional[list[str]] = None,
    create_if_missing: bool = False,
) -> int:
    """
    Generic CSV load: read CSV and insert into table_name.
    If columns is None, uses first row as column names.
    create_if_missing: not implemented here; create table manually or use create_bhav_copy_table.
    Returns number of rows inserted.
    """
    csv_path = Path(csv_path)
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()
    if columns:
        df = df[[c for c in columns if c in df.columns]]
    rows = [tuple(x) for x in df.to_numpy()]
    if not rows:
        return 0

    placeholders = ",".join([f":{i+1}" for i in range(len(df.columns))])
    col_list = ",".join(df.columns)
    insert_sql = f"INSERT INTO {table_name} ({col_list}) VALUES ({placeholders})"

    conn = get_connection()
    try:
        cursor = conn.cursor()
        for i in range(0, len(rows), ORACLE_BATCH_SIZE):
            batch = rows[i : i + ORACLE_BATCH_SIZE]
            cursor.executemany(insert_sql, batch)
        conn.commit()
        return len(rows)
    finally:
        conn.close()
