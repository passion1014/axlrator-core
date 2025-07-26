import google.generativeai as genai

genai.configure(api_key="AIzaSyB9Dh_UqsTh-T3iscFspDQ0Ic9ChkyOOBM")  # 여기에 발급받은 키를 넣으세요

model = genai.GenerativeModel("gemini-1.5-flash")

response = model.generate_content("안녕?")

print(response.text)