from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/')
def home():
    return "Welcome to Klein Jasper Agrabio's API!"

@app.route('/student')
def student():
    return jsonify({
        "student_id": "2026-00123",
        "name": "Klein Jasper Agrabio",
        "program": "BSIT",
        "year": 3,
        "section": "A"
    })

@app.route('/hello')
def say_hello():
    name = request.args.get('name', 'Student')

    return jsonify({
        "message": f"Hello, {name}!"
    })

# NEW ENDPOINT 1
@app.route('/course')
def course():
    return jsonify({
        "course_code": "IT 3120",
        "course_name": "Information Technology Laboratory",
        "instructor": "Rene D. Arduo"
    })

# NEW ENDPOINT 2
@app.route('/profile')
def profile():
    return jsonify({
        "name": "Klein Jasper Agrabio",
        "school": "ISU",
        "program": "BSIT",
        "year": 3,
        "section": "A"
    })

if __name__ == '__main__':
    app.run(debug=True)