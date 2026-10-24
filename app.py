
from flask import Flask, jsonify, request, render_template
import sqlite3
import requests
from pathlib import Path

app = Flask(__name__)
app.secret_key = "activity9-integration-secret-key"

DATABASE = Path(__file__).with_name("students.db")

PARTNER_API_URL = "https://balcenajessicaann.onrender.com/students"

# Set this only after your classmate confirms the actual POST endpoint.
PARTNER_POST_URL = None


def get_db():
    conn = sqlite3.connect(str(DATABASE))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create the table if missing and migrate old databases safely."""
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
        for row in conn.execute("PRAGMA table_info(students)").fetchall()
    }

    if "source" not in columns:
        conn.execute("""
            ALTER TABLE students
            ADD COLUMN source TEXT NOT NULL DEFAULT 'Local'
        """)

    conn.commit()
    conn.close()


# Run the migration when Gunicorn imports this module on Render.
init_db()


def normalize_student(data):
    if not isinstance(data, dict):
        return None

    student_id = data.get("student_id", "")
    name = data.get("name", data.get("fullname", ""))
    program = data.get("program", data.get("course", ""))
    year = data.get("year", 1)
    section = data.get("section", "A")

    if not student_id or not name or not program:
        return None

    try:
        year = int(year)
    except (TypeError, ValueError):
        return None

    return {
        "student_id": str(student_id),
        "name": str(name),
        "program": str(program),
        "year": year,
        "section": str(section)
    }


def fetch_partner_records():
    response = requests.get(PARTNER_API_URL, timeout=45)
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


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/student")
def student():
    return jsonify({
        "student_id": "2026-00123",
        "name": "Klein Jasper Agrabio",
        "program": "BSIT",
        "year": 3,
        "section": "A"
    })


@app.route("/hello")
def hello():
    return jsonify({
        "message": f"Hello, {request.args.get('name', 'World')}!"
    })


@app.route("/course")
def course():
    return jsonify({
        "course_code": "IT 3120",
        "course_name": "Information Technology Laboratory",
        "instructor": "Rene D. Arduo"
    })


@app.route("/profile")
def profile():
    return jsonify({
        "name": "Klein Jasper Agrabio",
        "program": "BSIT",
        "year": 3,
        "section": "A",
        "school": "ISUFST"
    })


@app.route("/students", methods=["GET"])
@app.route("/api/students", methods=["GET"])
def get_students():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM students ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])


@app.route("/students/<int:student_id>", methods=["GET"])
@app.route("/api/students/<int:student_id>", methods=["GET"])
def get_student(student_id):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM students WHERE id = ?", (student_id,)
    ).fetchone()
    conn.close()

    if row is None:
        return jsonify({"error": "Student not found"}), 404

    return jsonify(dict(row))


@app.route("/filter")
def filter_students():
    program = request.args.get("program", "")
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM students WHERE program LIKE ? ORDER BY id",
        (f"%{program}%",)
    ).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])


@app.route("/api/students", methods=["POST"])
def add_student():
    payload = request.get_json(silent=True) or {}
    data = normalize_student(payload)

    if not data:
        return jsonify({
            "error": "Provide student_id, name, program, year and section."
        }), 400

    source = str(payload.get("source", "External API"))

    conn = get_db()
    cursor = conn.execute("""
        INSERT INTO students
        (student_id, name, program, year, section, source)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        data["student_id"], data["name"], data["program"],
        data["year"], data["section"], source
    ))
    conn.commit()

    row = conn.execute(
        "SELECT * FROM students WHERE id = ?", (cursor.lastrowid,)
    ).fetchone()
    conn.close()

    return jsonify({
        "message": "Student created successfully",
        "student": dict(row)
    }), 201


@app.route("/api/students/<int:student_id>", methods=["PUT"])
def update_student(student_id):
    data = normalize_student(request.get_json(silent=True) or {})

    if not data:
        return jsonify({"error": "Invalid student data"}), 400

    conn = get_db()
    existing = conn.execute(
        "SELECT id FROM students WHERE id = ?", (student_id,)
    ).fetchone()

    if existing is None:
        conn.close()
        return jsonify({"error": "Student not found"}), 404

    conn.execute("""
        UPDATE students
        SET student_id=?, name=?, program=?, year=?, section=?
        WHERE id=?
    """, (
        data["student_id"], data["name"], data["program"],
        data["year"], data["section"], student_id
    ))
    conn.commit()

    row = conn.execute(
        "SELECT * FROM students WHERE id = ?", (student_id,)
    ).fetchone()
    conn.close()

    return jsonify({
        "message": "Student updated successfully",
        "student": dict(row)
    })


@app.route("/api/students/<int:student_id>", methods=["DELETE"])
def delete_student(student_id):
    conn = get_db()
    cursor = conn.execute(
        "DELETE FROM students WHERE id = ?", (student_id,)
    )
    conn.commit()
    conn.close()

    if cursor.rowcount == 0:
        return jsonify({"error": "Student not found"}), 404

    return jsonify({"message": "Student deleted successfully"})


@app.route("/partner-records", methods=["GET"])
@app.route("/api/classmate-records", methods=["GET"])
def partner_records():
    try:
        records = fetch_partner_records()
        valid_records = []

        for record in records:
            student = normalize_student(record)
            if student:
                valid_records.append(student)

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


@app.route("/import-student", methods=["POST"])
def import_student():
    payload = request.get_json(silent=True) or request.form.to_dict()
    data = normalize_student(payload)

    if not data:
        return jsonify({"error": "Invalid student record"}), 400

    conn = get_db()
    existing = conn.execute("""
        SELECT id FROM students
        WHERE student_id = ? AND source = 'Classmate API'
    """, (data["student_id"],)).fetchone()

    if existing:
        conn.close()
        return jsonify({
            "message": "This record was already imported",
            "local_id": existing["id"]
        }), 409

    cursor = conn.execute("""
        INSERT INTO students
        (student_id, name, program, year, section, source)
        VALUES (?, ?, ?, ?, ?, 'Classmate API')
    """, (
        data["student_id"], data["name"], data["program"],
        data["year"], data["section"]
    ))
    conn.commit()

    row = conn.execute(
        "SELECT * FROM students WHERE id = ?", (cursor.lastrowid,)
    ).fetchone()
    conn.close()

    return jsonify({
        "message": "Partner record saved to your database",
        "student": dict(row)
    }), 201


@app.route("/send-to-partner", methods=["POST"])
def send_to_partner():
    payload = request.get_json(silent=True) or request.form.to_dict()
    data = normalize_student(payload)

    if not data:
        return jsonify({"error": "Invalid student record"}), 400

    if not PARTNER_POST_URL:
        return jsonify({
            "error": "Partner POST endpoint is not configured",
            "message": (
                "Ask your classmate for the actual POST URL. "
                "The /students URL has only been verified for GET."
            )
        }), 501

    outgoing = dict(data)
    outgoing["source"] = "External API"

    try:
        response = requests.post(
            PARTNER_POST_URL, json=outgoing, timeout=45
        )

        try:
            result = response.json()
        except ValueError:
            result = response.text[:1000]

        if not response.ok:
            return jsonify({
                "error": "Partner rejected the record",
                "partner_status": response.status_code,
                "partner_response": result
            }), 502

        return jsonify({
            "message": "Record sent to partner successfully",
            "partner_status": response.status_code,
            "partner_response": result
        })

    except requests.RequestException as error:
        return jsonify({
            "error": "Could not send record to partner",
            "details": str(error)
        }), 502


@app.route("/integration-dashboard")
def integration_dashboard():
    # Ensure this database schema is migrated before querying.
    init_db()

    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM students ORDER BY id DESC"
    ).fetchall()

    counts = conn.execute("""
        SELECT
            SUM(CASE WHEN source = 'Local' THEN 1 ELSE 0 END) AS local_count,
            SUM(CASE WHEN source = 'Classmate API' THEN 1 ELSE 0 END) AS imported_count,
            SUM(CASE WHEN source = 'External API' THEN 1 ELSE 0 END) AS external_count
        FROM students
    """).fetchone()
    conn.close()

    return jsonify({
        "local_records": counts["local_count"] or 0,
        "imported_records": counts["imported_count"] or 0,
        "external_api_records": counts["external_count"] or 0,
        "records": [dict(row) for row in rows]
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
