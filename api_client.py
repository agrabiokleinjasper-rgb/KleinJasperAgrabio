
import requests

url = "https://kleinjasperagrabio.onrender.com/course"

response = requests.get(url)

if response.status_code == 200:
    data = response.json()

    print("Course Code:", data["course_code"])
    print("Course Name:", data["course_name"])
    print("Instructor:", data["instructor"])
else:
    print("Request failed.")
    print("Status Code:", response.status_code)
