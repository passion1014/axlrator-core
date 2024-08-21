import cx_Oracle
import psycopg2

# Oracle 테이블 스키마 읽기
# def get_oracle_schema(connection_str, schema_name):
#     connection = cx_Oracle.connect(connection_str)
#     cursor = connection.cursor()
#     query = f"""
#     SELECT table_name, column_name, data_type
#     FROM all_tab_columns
#     WHERE owner = '{schema_name.upper()}'
#     """
#     cursor.execute(query)
#     schema = {}
#     for row in cursor.fetchall():
#         table, column, data_type = row
#         if table not in schema:
#             schema[table] = []
#         schema[table].append((column, data_type))
#     cursor.close()
#     connection.close()
#     return schema

# PostgreSQL 테이블 스키마 읽기
def get_postgresql_schema(connection_str, schema_name):
    connection = psycopg2.connect(connection_str)
    cursor = connection.cursor()
    query = f"""
    SELECT table_name, column_name, data_type
    FROM information_schema.columns
    -- WHERE table_schema = '{schema_name}'
    """
    cursor.execute(query)
    schema = {}
    for row in cursor.fetchall():
        table, column, data_type = row
        if table not in schema:
            schema[table] = []
        schema[table].append((column, data_type))
    cursor.close()
    connection.close()
    return schema

# 결과 출력 및 프롬프트용 포맷
def format_schema_for_prompt(schema):
    formatted = "Tables:\n"
    for table, columns in schema.items():
        formatted += f"- {table}("
        formatted += ", ".join([f"{col[0]} {col[1]}" for col in columns])
        formatted += ")\n"
    return formatted


if __name__ == '__main__':
    oracle_conn_str = "user/password@host:port/service"
    postgres_conn_str = "dbname=ragserver user=ragserver password=ragserver host=localhost port=5432"
    # oracle_schema = get_oracle_schema(oracle_conn_str, 'your_schema_name')
    postgres_schema = get_postgresql_schema(postgres_conn_str, 'your_schema_name')

    # print("Oracle Schema:")
    # print(format_schema_for_prompt(oracle_schema))
    print("\nPostgreSQL Schema:")
    print(format_schema_for_prompt(postgres_schema))

