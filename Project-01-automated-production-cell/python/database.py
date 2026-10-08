import sqlite3


connection = sqlite3.connect("data/production.db")

cursor = connection.cursor()

cursor.execute("""
"INSERT INTO production (result, timestamp) VALUES (?, ?)",
    (inspection_result, datetime.now().isoformat())
)
""")

connection.commit()
connection.close()

print("Database ready.")