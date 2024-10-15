import requests

response = requests.post("http://localhost:8000/plugin/api/sql", json={"question": "SELECT * FROM users;"})
print(response.json())