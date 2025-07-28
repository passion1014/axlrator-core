import os
from dotenv import load_dotenv
import google.generativeai as genai

# 환경변수 파일 로드
load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")

genai.configure(api_key=api_key)

try:
    model = genai.GenerativeModel("gemini-1.5-flash")
    print("✅ 프롬프트 전송 중................")

    response = model.generate_content("""
Determine whether a document search in the vector database is necessary for the following question.
Respond with ‘yes’ if needed, ‘no’ otherwise.
- The vector database contains source code of a securities trading system.

Question:
처음 물어본 내용을 알려줘
""")
    print("텍스트 응답:", response.text)
except Exception as e:
    print("❗️에러 발생:", e)