
import sqlite3
from pathlib import Path

db = Path("jay01_history.sqlite3")

connection = sqlite3.connect(
    f"file:{db.resolve().as_posix()}?mode=ro",
    uri=True,
)

try:
    for table, in connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ):
        if table == "sqlite_sequence":
            continue

        print(f"\n--- {table} ---")

        schema = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
            (table,),
        ).fetchone()

        print(schema[0] if schema else "Schema unavailable")

        columns = connection.execute(
            f'PRAGMA table_info("{table}")'
        ).fetchall()

        print("Columns:", [column[1] for column in columns])
finally:
    connection.close()
