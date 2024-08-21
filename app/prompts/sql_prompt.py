from langchain_core.prompts import ChatPromptTemplate, PromptTemplate



SQL_QUERY_PROMPT = PromptTemplate.from_template("""
You are an expert SQL query generator. 
You will convert Korean text into an accurate SQL query. 
First, translate the input Korean sentence into English. 
Then think in English to determine the proper SQL query. 
Finally, output the SQL query directly in SQL syntax.

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


TABLE_SCHEMA_QUERY_PROMPT = PromptTemplate.from_template("""
You are a database schema extractor. 
Your job is to analyze the user's question in Korean and identify the relevant tables and columns required to answer the question. 
The question might refer to multiple tables and columns.

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