
import sqlite3

conn = sqlite3.connect('students.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    name TEXT NOT NULL,
    program TEXT NOT NULL,
    year INTEGER NOT NULL,
    section TEXT NOT NULL
)
''')

cursor.execute("DELETE FROM students")

students = [
    ('2026-00123', 'Klein Jasper Agrabio', 'BSIT', 3, 'A'),
    ('2026-00124', 'Maria Santos', 'BSIT', 3, 'A'),
    ('2026-00125', 'Pedro Reyes', 'BSIT', 3, 'B'),
    ('2026-00126', 'Ana Cruz', 'BSCS', 2, 'A'),
    ('2026-00127', 'John Dela Cruz', 'BSCS', 1, 'B')
]

cursor.executemany('''
INSERT INTO students (student_id, name, program, year, section)
VALUES (?, ?, ?, ?, ?)
''', students)

conn.commit()
conn.close()

print("Database created successfully.")
