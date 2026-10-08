import sqlite3

connection = sqlite3.connect("data/production.db")
cursor = connection.cursor()

cursor.execute("""
SELECT
    COUNT(*) AS total,
    SUM(CASE WHEN result = 'OK' THEN 1 ELSE 0 END) AS ok_count,
    SUM(CASE WHEN result = 'DEFECT' THEN 1 ELSE 0 END) AS defect_count
FROM production
WHERE timestamp IS NOT NULL
""")

total, ok_count, defect_count = cursor.fetchone()

defect_rate = (defect_count / total) * 100 if total else 0

print("=== Production Report ===")
print(f"Total parts : {total}")
print(f"OK parts    : {ok_count}")
print(f"Defects     : {defect_count}")
print(f"Defect rate : {defect_rate:.2f}%")

connection.close()