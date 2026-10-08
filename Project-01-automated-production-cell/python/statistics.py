def get_production_statistics(connection):
    """Calculate production statistics from the SQLite database."""

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN result = 'OK' THEN 1 ELSE 0 END) AS ok,
            SUM(CASE WHEN result = 'DEFECT' THEN 1 ELSE 0 END) AS defect
        FROM production
        WHERE timestamp IS NOT NULL
    """)

    total, ok, defect = cursor.fetchone()

    total = total or 0
    ok = ok or 0
    defect = defect or 0

    defect_rate = (defect / total * 100) if total > 0 else 0

    return total, ok, defect, defect_rate
