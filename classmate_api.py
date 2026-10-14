
import requests

url = "https://balcenajessicaann.onrender.com/student"

response = requests.get(url, timeout=30)

print("Status Code:", response.status_code)

if response.status_code == 200:
    data = response.json()

    print("Classmate API Data:")
    for key, value in data.items():
        print(f"{key}: {value}")
else:
    print("Request failed.")
    print("Status Code:", response.status_code)
    print(response.text)
