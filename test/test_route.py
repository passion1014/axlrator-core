import requests

response = requests.post("http://localhost:8000/plugin/api/sql", json={"question": "보증 조회 쿼리"})
print(response.json())

response = requests.post("http://localhost:8000/plugin/api/code", json={"question": "윤달 프로그램을 작성해줘"})
print(response.json())