
from flask import Flask, jsonify, request, render_template
import sqlite3
import requests

app = Flask(__name__)

DATABASE = "students.db"

# Classmate API: sinusubukan ang ilang posibleng endpoint.
# Ang tamang endpoint ay depende sa aktuwal na API ng kaklase mo.
CLASSMATE_API_URLS = [
    "https://balcenajessicaann.onrender.com/api/students",
    "https://balcenajessicaann.onrender.com/students",
    "https://balcenajessicaann.onrender.com/student",
]


# -------------------------
# DATABASE CONNECTION
# -------------------------

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# -------------------------
# HOME PAGE
# -------------------------

@app.route("/")
def home():
    return render_template("index.html")


# -------------------------
# EXISTING API ENDPOINTS
# -------------------------

@app.route("/student", methods=["GET"])
def student():
    return jsonify({
        "student_id": "2026-00123",
        "name": "Klein Jasper Agrabio",
        "program": "BSIT",
        "year": 3,
        "section": "A"
    })


@app.route("/hello", methods=["GET"])
def say_hello():
    name = request.args.get("name", "Student")
    return jsonify({"message": f"Hello, {name}!"})


@app.route("/course", methods=["GET"])
def course():
    return jsonify({
        "course_code": "IT 3120",
        "course_name": "Information Technology Laboratory",
        "instructor": "Rene D. Arduo"
    })


@app.route("/profile", methods=["GET"])
def profile():
    return jsonify({
        "name": "Klein Jasper Agrabio",
        "school": "ISUFST",
        "program": "BSIT",
        "year": 3,
        "section": "A"
    })


# -------------------------
# READ: GET ALL STUDENTS
# -------------------------

@app.route("/students", methods=["GET"])
def get_students():
    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM students ORDER BY id"
        ).fetchall()

        return jsonify([dict(row) for row in rows])
    finally:
        conn.close()


# -------------------------
# READ: GET ONE STUDENT
# -------------------------

@app.route("/students/<int:id>", methods=["GET"])
def get_student(id):
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT * FROM students WHERE id = ?", (id,)
        ).fetchone()

        if row is None:
            return jsonify({"error": "Student not found"}), 404

        return jsonify(dict(row))
    finally:
        conn.close()


# -------------------------
# FILTER STUDENTS BY PROGRAM
# -------------------------

@app.route("/filter", methods=["GET"])
def filter_students():
    program = request.args.get("program", "").strip()

    if not program:
        return jsonify({
            "error": "Please provide a program, e.g. ?program=BSIT"
        }), 400

    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM students WHERE program = ? ORDER BY id",
            (program,)
        ).fetchall()

        return jsonify([dict(row) for row in rows])
    finally:
        conn.close()


# -------------------------
# CREATE: ADD STUDENT
# -------------------------

@app.route("/api/students", methods=["POST"])
def add_student():
    data = request.get_json(silent=True) or {}

    required = ["student_id", "name", "program", "year", "section"]

    if any(
        data.get(key) is None or str(data.get(key)).strip() == ""
        for key in required
    ):
        return jsonify({"error": "All student fields are required"}), 400

    try:
        year = int(data["year"])

        conn = get_db_connection()
        try:
            cursor = conn.execute(
                """
                INSERT INTO students
                (student_id, name, program, year, section)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    str(data["student_id"]).strip(),
                    str(data["name"]).strip(),
                    str(data["program"]).strip(),
                    year,
                    str(data["section"]).strip()
                )
            )
            conn.commit()

            return jsonify({
                "message": "Student added successfully",
                "id": cursor.lastrowid
            }), 201
        finally:
            conn.close()

    except (ValueError, TypeError):
        return jsonify({"error": "Year must be a number"}), 400
    except sqlite3.IntegrityError:
        return jsonify({
            "error": "Student ID already exists or violates a database rule"
        }), 409


# -------------------------
# READ: GET ONE STUDENT (CRUD API)
# -------------------------

@app.route("/api/students/<int:id>", methods=["GET"])
def api_get_student(id):
    return get_student(id)


# -------------------------
# UPDATE: EDIT STUDENT
# -------------------------

@app.route("/api/students/<int:id>", methods=["PUT"])
def update_student(id):
    data = request.get_json(silent=True) or {}

    required = ["student_id", "name", "program", "year", "section"]

    if any(
        data.get(key) is None or str(data.get(key)).strip() == ""
        for key in required
    ):
        return jsonify({"error": "All student fields are required"}), 400

    try:
        year = int(data["year"])

        conn = get_db_connection()
        try:
            cursor = conn.execute(
                """
                UPDATE students
                SET student_id = ?, name = ?, program = ?,
                    year = ?, section = ?
                WHERE id = ?
                """,
                (
                    str(data["student_id"]).strip(),
                    str(data["name"]).strip(),
                    str(data["program"]).strip(),
                    year,
                    str(data["section"]).strip(),
                    id
                )
            )
            conn.commit()

            if cursor.rowcount == 0:
                return jsonify({"error": "Student not found"}), 404

            return jsonify({"message": "Student updated successfully"})
        finally:
            conn.close()

    except (ValueError, TypeError):
        return jsonify({"error": "Year must be a number"}), 400
    except sqlite3.IntegrityError:
        return jsonify({
            "error": "Student ID already exists or violates a database rule"
        }), 409


# -------------------------
# DELETE: REMOVE STUDENT
# -------------------------

@app.route("/api/students/<int:id>", methods=["DELETE"])
def delete_student(id):
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            "DELETE FROM students WHERE id = ?", (id,)
        )
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Student not found"}), 404

        return jsonify({"message": "Student deleted successfully"})
    finally:
        conn.close()


# -------------------------
# GET RECORDS FROM CLASSMATE API
# -------------------------

@app.route("/api/classmate-records", methods=["GET"])
def get_classmate_records():
    errors = []

    for api_url in CLASSMATE_API_URLS:
        try:
            response = requests.get(api_url, timeout=15)

            if response.status_code != 200:
                errors.append(
                    f"{api_url} returned HTTP {response.status_code}"
                )
                continue

            try:
                data = response.json()
            except ValueError:
                errors.append(f"{api_url} did not return valid JSON")
                continue

            # Iba't ibang API ay maaaring magbalik ng list o object.
            records = data

            if isinstance(data, dict):
                for key in ("students", "records", "data", "results"):
                    if isinstance(data.get(key), list):
                        records = data[key]
                        break

            return jsonify({
                "message": "Classmate API retrieved successfully",
                "source": api_url,
                "records": records
            }), 200

        except requests.RequestException as error:
            errors.append(f"{api_url}: {str(error)}")

    app.logger.warning("Classmate API errors: %s", errors)

    return jsonify({
        "error": "Unable to retrieve classmate records.",
        "details": errors
    }), 502


# -------------------------
# RUN APPLICATION
# -------------------------

if __name__ == "__main__":
    app.run(debug=True)
