
import sqlite3

DATABASE = "students.db"

def init_db():
    conn = sqlite3.connect(DATABASE)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            name TEXT NOT NULL,
            program TEXT NOT NULL,
            year INTEGER NOT NULL,
            section TEXT NOT NULL,
            source TEXT DEFAULT 'Local'
        )
    """)

    columns = [
        row[1] for row in conn.execute("PRAGMA table_info(students)")
    ]

    if "source" not in columns:
        conn.execute(
            "ALTER TABLE students ADD COLUMN source TEXT DEFAULT 'Local'"
        )

    # Reset sample data for the laboratory setup.
    conn.execute("DELETE FROM students")
    conn.execute("DELETE FROM sqlite_sequence WHERE name = 'students'")

    sample_students = [
        ("2026-00123", "Klein Jasper Agrabio", "BSIT", 3, "A", "Local"),
        ("2026-00124", "Maria Santos", "BSIT", 3, "A", "Local"),
        ("2026-00125", "Pedro Reyes", "BSIT", 3, "B", "Local"),
        ("2026-00126", "Ana Cruz", "BSCS", 2, "A", "Local"),
        ("2026-00127", "John Dela Cruz", "BSCS", 1, "B", "Local")
    ]

    conn.executemany("""
        INSERT INTO students
        (student_id, name, program, year, section, source)
        VALUES (?, ?, ?, ?, ?, ?)
    """, sample_students)

    conn.commit()
    conn.close()
    print("Database initialized successfully.")

if __name__ == "__main__":
    init_db()
