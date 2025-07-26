
import os
import google.generativeai as genai

genai.configure(api_key="")

try:
    model = genai.GenerativeModel("gemini-1.5-flash")
    print("✅ 프롬프트 전송 중................")
    response = model.generate_content("안녕?")
    print("✅ 응답 도착")
    print("전체 응답 객체:", response)
    print("텍스트 응답:", response.text)
except Exception as e:
    print("❗️에러 발생:", e)