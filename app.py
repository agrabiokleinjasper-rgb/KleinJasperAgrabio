
from flask import Flask, jsonify, request, render_template
import sqlite3

app = Flask(__name__)


# SQLite database connection
def get_db_connection():
    conn = sqlite3.connect('students.db')
    conn.row_factory = sqlite3.Row
    return conn


# Home page
@app.route('/')
def home():
    return render_template('index.html')


# Activity 6: Student information
@app.route('/student')
def student():
    return jsonify({
        "student_id": "2026-00123",
        "name": "Klein Jasper Agrabio",
        "program": "BSIT",
        "year": 3,
        "section": "A"
    })


# Activity 6: Greeting
@app.route('/hello')
def say_hello():
    name = request.args.get('name', 'Student')
    return jsonify({
        "message": f"Hello, {name}!"
    })


# Activity 6: Course information
@app.route('/course')
def course():
    return jsonify({
        "course_code": "IT 3120",
        "course_name": "Information Technology Laboratory",
        "instructor": "Rene D. Arduo"
    })


# Activity 6: Profile
@app.route('/profile')
def profile():
    return jsonify({
        "name": "Klein Jasper Agrabio",
        "school": "ISUFST",
        "program": "BSIT",
        "year": 3,
        "section": "A"
    })


# Activity 7: Get all students from the database
@app.route('/students')
def get_students():
    conn = get_db_connection()
    students = conn.execute(
        'SELECT * FROM students ORDER BY id'
    ).fetchall()
    conn.close()

    return jsonify([dict(student) for student in students])


# Activity 7: Get one student by database ID
@app.route('/students/<int:student_id>')
def get_student(student_id):
    conn = get_db_connection()
    student_record = conn.execute(
        'SELECT * FROM students WHERE id = ?',
        (student_id,)
    ).fetchone()
    conn.close()

    if student_record is None:
        return jsonify({
            "error": "Student not found"
        }), 404

    return jsonify(dict(student_record))


# Additional Activity 7 endpoint:
# Filter students by program, year, or section.
# Examples: /filter?program=BSIT
#           /filter?year=3
#           /filter?section=A
@app.route('/filter')
def filter_students():
    program = request.args.get('program')
    year = request.args.get('year')
    section = request.args.get('section')

    conditions = []
    values = []

    if program:
        conditions.append('program = ?')
        values.append(program)

    if year:
        try:
            values.append(int(year))
            conditions.append('year = ?')
        except ValueError:
            return jsonify({
                "error": "Year must be a number"
            }), 400

    if section:
        conditions.append('section = ?')
        values.append(section)

    if not conditions:
        return jsonify({
            "error": "Provide program, year, or section"
        }), 400

    query = 'SELECT * FROM students WHERE ' + ' AND '.join(conditions)
    query += ' ORDER BY id'

    conn = get_db_connection()
    students = conn.execute(query, values).fetchall()
    conn.close()

    return jsonify([dict(student) for student in students])


if __name__ == '__main__':
    app.run(debug=True)
