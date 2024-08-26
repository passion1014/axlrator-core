from langchain_core.prompts import ChatPromptTemplate, PromptTemplate



# 당신은 SQL 쿼리 생성 전문가입니다.
# 한국어 텍스트를 정확한 SQL 쿼리로 변환합니다.
# 먼저, 입력된 한국어 문장을 영어로 번역합니다.
# 그런 다음 영어로 생각하여 적절한 SQL 쿼리를 결정합니다.
# 마지막으로 SQL 쿼리를 SQL 구문으로 직접 출력합니다.

# 데이터베이스 스키마는 다음과 같습니다.
# {database_schema}

# 한국어 사용자 요청은 다음과 같습니다.
# {question}

# 1단계: 한국어 문장을 영어로 번역합니다.
# 2단계: 이 요청에 대한 SQL 쿼리를 작성하는 방법에 대해 영어로 생각합니다.
# 3단계: 최종 SQL 쿼리를 제공합니다.

# 출력 형식:
# ```sql
# [생성된 SQL 쿼리]

SQL_QUERY_PROMPT = PromptTemplate.from_template("""
You are an expert SQL query generator. 
You will convert Korean text into an accurate SQL query. 
First, translate the input Korean sentence into English. 
Then think in English to determine the proper SQL query. 
Finally, output the SQL query directly in SQL syntax.
모든 답변은 한국어로 답변해줘

Here is the database schema:
{database_schema}

The user request in Korean is:
{question}

Step 1: Translate the Korean sentence into English.
Step 2: Think in English about how to write the SQL query for this request.
Step 3: Provide the final SQL query. 

Output format:
```sql
[Generated SQL query]

""")



# 당신은 데이터베이스 스키마 추출자입니다.
# 당신의 일은 사용자의 한국어 질문을 분석하고 질문에 답하는 데 필요한 관련 테이블과 열을 식별하는 것입니다.
# 질문은 여러 테이블과 열을 참조할 수 있습니다.

# 데이터베이스 스키마는 다음과 같습니다.
# {database_schema}

# 한국어 사용자 요청은 다음과 같습니다.
# {question}

# 1단계: 한국어 질문을 영어로 번역합니다.
# 2단계: 요청을 충족하는 데 필요한 테이블과 열을 식별합니다.
# 3단계: 식별된 테이블과 열을 구조화된 형식으로 나열합니다.

# 출력 형식:
# - 테이블: [관련 테이블]
# - 열: [관련 열]

TABLE_SCHEMA_QUERY_PROMPT = PromptTemplate.from_template("""
You are a database schema extractor. 
Your job is to analyze the user's question in Korean and identify the relevant tables and columns required to answer the question. 
The question might refer to multiple tables and columns.
모든 답변은 한국어로 답변해줘

Here is the database schema:
{database_schema}

The user request in Korean is:
{question}

Step 1: Translate the Korean question into English.
Step 2: Identify the tables and columns required to satisfy the request.
Step 3: List the identified tables and columns in a structured format.

Output format:
- Tables: [Relevant tables]
- Columns: [Relevant columns]

""")




############################################################
