import sqlite3
from datetime import datetime


connection = sqlite3.connect("data/production.db")
cursor = connection.cursor()

cursor.execute("""
ALTER TABLE production
ADD COLUMN timestamp TEXT
""")

connection.commit()
connection.close()

print("Timestamp column added.")
