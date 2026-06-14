from datetime import datetime, timedelta
import oracledb
import subprocess
from config import ORACLE_USER, ORACLE_PASSWORD, ORACLE_DSN

conn = oracledb.connect(
    user=ORACLE_USER,
    password=ORACLE_PASSWORD,
    dsn=ORACLE_DSN
)

cursor = conn.cursor()

cursor.execute("""
    select max(TRADDT) from nse_bhav_copy
""")

last_loaded_date = cursor.fetchone()[0]

if last_loaded_date is None:
    raise Exception("No load history found.")
# print(last_loaded_date)
start_date = last_loaded_date.date() + timedelta(days=1)
end_date = datetime.today().date()
# print(start_date)
# print(end_date)


while start_date <= end_date:

    # Skip Saturday (5) and Sunday (6)

    process_date = start_date.strftime("%Y-%m-%d")

    print(f"Loading data for {process_date}")

    try:
        result = subprocess.run(
            ["python", "load_main.py", "--date", process_date],
            capture_output=True,
            text=True
        )

        output = (result.stdout or "") + (result.stderr or "")

        if "Download failed. Check date (trading day) and network" in output:
            print(f"No trading data for {process_date}. Skipping...")
        elif result.returncode != 0:
            print(f"Error processing {process_date}")
            print(output)
            raise Exception(f"load_main.py failed for {process_date}")

    except Exception as e:
        print(f"Unexpected error for {process_date}: {e}")
        raise

    start_date += timedelta(days=1)

cursor.close()
conn.close()