
import os
import sqlite3
import requests
from pathlib import Path
from flask import Flask, jsonify, request, render_template

app = Flask(__name__)
app.secret_key = os.environ.get(
    "SECRET_KEY", "activity9-integration-secret-key"
)

# ==================================================
# CONFIGURATION
# ==================================================

DATABASE = Path(__file__).with_name("students.db")

# Classmate's GET endpoint
PARTNER_API_URL = os.environ.get(
    "PARTNER_API_URL",
    "https://balcenajessicaann-2axr.onrender.com/students"
)

# Classmate's POST endpoint
# Confirm that the classmate's API supports POST here.
PARTNER_POST_URL = os.environ.get(
    "PARTNER_POST_URL",
    "https://balcenajessicaann-2axr.onrender.com/api/students"
)


# ==================================================
# DATABASE
# ==================================================

def get_db():
    conn = sqlite3.connect(str(DATABASE), timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            name TEXT NOT NULL,
            program TEXT NOT NULL,
            year INTEGER NOT NULL,
            section TEXT NOT NULL,
            source TEXT NOT NULL DEFAULT 'Local'
        )
    """)

    columns = {
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(students)"
        ).fetchall()
    }

    if "source" not in columns:
        conn.execute("""
            ALTER TABLE students
            ADD COLUMN source TEXT NOT NULL DEFAULT 'Local'
        """)

    conn.commit()
    conn.close()


init_db()


# ==================================================
# VALIDATE STUDENT DATA
# ==================================================

def normalize_student(data):
    if not isinstance(data, dict):
        return None

    student_id = data.get("student_id", "")
    name = data.get("name", data.get("fullname", ""))
    program = data.get("program", data.get("course", ""))
    year = data.get("year", 1)
    section = data.get("section", "A")

    if not all([
        str(student_id).strip(),
        str(name).strip(),
        str(program).strip(),
        str(section).strip()
    ]):
        return None

    try:
        year = int(year)
    except (TypeError, ValueError):
        return None

    if year < 1 or year > 6:
        return None

    return {
        "student_id": str(student_id).strip(),
        "name": str(name).strip(),
        "program": str(program).strip(),
        "year": year,
        "section": str(section).strip()
    }


# ==================================================
# SAVE A STUDENT LOCALLY
# ==================================================

def save_student(data, source="Local"):
    conn = get_db()

    cursor = conn.execute("""
        INSERT INTO students
        (student_id, name, program, year, section, source)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        data["student_id"],
        data["name"],
        data["program"],
        data["year"],
        data["section"],
        source
    ))

    conn.commit()

    row = conn.execute(
        "SELECT * FROM students WHERE id = ?",
        (cursor.lastrowid,)
    ).fetchone()

    student = dict(row)
    conn.close()

    return student


# ==================================================
# HOME PAGE
# ==================================================

@app.route("/")
def home():
    return render_template("index.html")


# ==================================================
# SAMPLE API ENDPOINTS
# ==================================================

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
def hello():
    name = request.args.get("name", "World")
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
        "program": "BSIT",
        "year": 3,
        "section": "A",
        "school": "ISUFST"
    })


# ==================================================
# GET ALL LOCAL STUDENTS
# ==================================================

@app.route("/students", methods=["GET"])
@app.route("/api/students", methods=["GET"])
def get_students():
    conn = get_db()

    rows = conn.execute("""
        SELECT * FROM students ORDER BY id DESC
    """).fetchall()

    conn.close()

    return jsonify([dict(row) for row in rows])


# ==================================================
# GET ONE STUDENT BY DATABASE ID
# ==================================================

@app.route("/students/<int:student_id>", methods=["GET"])
@app.route("/api/students/<int:student_id>", methods=["GET"])
def get_student(student_id):
    conn = get_db()

    row = conn.execute(
        "SELECT * FROM students WHERE id = ?",
        (student_id,)
    ).fetchone()

    conn.close()

    if row is None:
        return jsonify({"error": "Student not found"}), 404

    return jsonify(dict(row))


# ==================================================
# ADD A STUDENT TO YOUR LOCAL DATABASE
# ==================================================

@app.route("/api/students", methods=["POST"])
def add_student():
    payload = request.get_json(silent=True) or {}
    data = normalize_student(payload)

    if not data:
        return jsonify({
            "error": (
                "Provide valid student_id, name, program, "
                "year and section."
            )
        }), 400

    source = str(payload.get("source", "Local"))

    student_record = save_student(data, source)

    return jsonify({
        "message": "Student created successfully",
        "student": student_record
    }), 201


# ==================================================
# UPDATE A LOCAL STUDENT
# ==================================================

@app.route("/api/students/<int:student_id>", methods=["PUT"])
def update_student(student_id):
    payload = request.get_json(silent=True) or {}
    data = normalize_student(payload)

    if not data:
        return jsonify({
            "error": "Invalid student data"
        }), 400

    conn = get_db()

    existing = conn.execute(
        "SELECT id FROM students WHERE id = ?",
        (student_id,)
    ).fetchone()

    if existing is None:
        conn.close()
        return jsonify({"error": "Student not found"}), 404

    conn.execute("""
        UPDATE students
        SET student_id = ?,
            name = ?,
            program = ?,
            year = ?,
            section = ?
        WHERE id = ?
    """, (
        data["student_id"],
        data["name"],
        data["program"],
        data["year"],
        data["section"],
        student_id
    ))

    conn.commit()

    row = conn.execute(
        "SELECT * FROM students WHERE id = ?",
        (student_id,)
    ).fetchone()

    conn.close()

    return jsonify({
        "message": "Student updated successfully",
        "student": dict(row)
    })


# ==================================================
# DELETE A LOCAL STUDENT
# ==================================================

@app.route("/api/students/<int:student_id>", methods=["DELETE"])
def delete_student(student_id):
    conn = get_db()

    cursor = conn.execute(
        "DELETE FROM students WHERE id = ?",
        (student_id,)
    )

    conn.commit()
    conn.close()

    if cursor.rowcount == 0:
        return jsonify({"error": "Student not found"}), 404

    return jsonify({
        "message": "Student deleted successfully"
    })


# ==================================================
# FILTER LOCAL STUDENTS BY PROGRAM
# ==================================================

@app.route("/filter", methods=["GET"])
def filter_students():
    program = request.args.get("program", "")

    conn = get_db()

    rows = conn.execute("""
        SELECT * FROM students
        WHERE program LIKE ?
        ORDER BY id DESC
    """, (f"%{program}%",)).fetchall()

    conn.close()

    return jsonify([dict(row) for row in rows])


# ==================================================
# GET STUDENTS FROM CLASSMATE'S API
# ==================================================

def fetch_partner_records():
    response = requests.get(
        PARTNER_API_URL,
        timeout=60
    )

    response.raise_for_status()
    payload = response.json()

    if isinstance(payload, list):
        return payload

    if isinstance(payload, dict):
        for key in ("students", "records", "data", "results"):
            if isinstance(payload.get(key), list):
                return payload[key]

        if "student_id" in payload and "name" in payload:
            return [payload]

    return []


@app.route("/partner-records", methods=["GET"])
@app.route("/api/classmate-records", methods=["GET"])
def partner_records():
    try:
        records = fetch_partner_records()
        valid_records = []

        for record in records:
            student_data = normalize_student(record)

            if student_data:
                valid_records.append(student_data)

        return jsonify({
            "message": "Partner records retrieved successfully",
            "source": PARTNER_API_URL,
            "count": len(valid_records),
            "records": valid_records
        })

    except requests.RequestException as error:
        return jsonify({
            "error": "Unable to retrieve partner records",
            "details": str(error),
            "partner_url": PARTNER_API_URL
        }), 502

    except ValueError as error:
        return jsonify({
            "error": "Partner API returned invalid JSON",
            "details": str(error)
        }), 502


# ==================================================
# IMPORT A CLASSMATE'S RECORD INTO YOUR DATABASE
# ==================================================

@app.route("/import-student", methods=["POST"])
def import_student():
    payload = request.get_json(silent=True)

    if payload is None:
        payload = request.form.to_dict()

    data = normalize_student(payload)

    if not data:
        return jsonify({
            "error": "Invalid student record"
        }), 400

    conn = get_db()

    existing = conn.execute("""
        SELECT id FROM students
        WHERE student_id = ?
          AND source = 'Classmate API'
    """, (data["student_id"],)).fetchone()

    conn.close()

    if existing:
        return jsonify({
            "message": "This record was already imported",
            "local_id": existing["id"]
        }), 409

    student_record = save_student(
        data,
        source="Classmate API"
    )

    return jsonify({
        "message": "Partner record saved to your database",
        "student": student_record
    }), 201


# ==================================================
# SEND A PRACTICE RECORD TO ANOTHER API
# ==================================================

@app.route("/send-to-partner", methods=["POST"])
def send_to_partner():
    payload = request.get_json(silent=True)

    if payload is None:
        payload = request.form.to_dict()

    data = normalize_student(payload)

    if not data:
        return jsonify({
            "error": (
                "Invalid student record. Provide student_id, "
                "name, program, year and section."
            )
        }), 400

    if not PARTNER_POST_URL:
        return jsonify({
            "error": "Partner POST URL is not configured"
        }), 500

    outgoing = dict(data)
    outgoing["source"] = "External API"

    try:
        response = requests.post(
            PARTNER_POST_URL,
            json=outgoing,
            headers={"Accept": "application/json"},
            timeout=60
        )

        try:
            result = response.json()
        except ValueError:
            result = response.text[:1000]

        if not response.ok:
            return jsonify({
                "error": "Partner rejected the record",
                "partner_status": response.status_code,
                "partner_url": PARTNER_POST_URL,
                "partner_response": result
            }), 502

        return jsonify({
            "message": "Record sent to partner successfully",
            "partner_status": response.status_code,
            "partner_url": PARTNER_POST_URL,
            "partner_response": result
        }), 200

    except requests.RequestException as error:
        return jsonify({
            "error": "Could not send record to partner",
            "partner_url": PARTNER_POST_URL,
            "details": str(error)
        }), 502


# ==================================================
# INTEGRATION DASHBOARD DATA
# ==================================================

@app.route("/integration-dashboard", methods=["GET"])
def integration_dashboard():
    conn = get_db()

    rows = conn.execute("""
        SELECT * FROM students ORDER BY id DESC
    """).fetchall()

    counts = conn.execute("""
        SELECT
            SUM(CASE WHEN source = 'Local'
                THEN 1 ELSE 0 END) AS local_count,
            SUM(CASE WHEN source = 'Classmate API'
                THEN 1 ELSE 0 END) AS imported_count,
            SUM(CASE WHEN source = 'External API'
                THEN 1 ELSE 0 END) AS external_count
        FROM students
    """).fetchone()

    conn.close()

    return jsonify({
        "local_records": counts["local_count"] or 0,
        "imported_records": counts["imported_count"] or 0,
        "external_api_records": counts["external_count"] or 0,
        "records": [dict(row) for row in rows]
    })


# ==================================================
# RUN FLASK
# ==================================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=True
    )
