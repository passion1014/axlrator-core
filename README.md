# AIFRED Server Guide

## 설치방법

```bash
# server 가상환경 생성 및 활성화
python -m venv server 
source server/bin/activate

 # 필요 라이브러리 설치
pip install -r requirements.txt

# 일반 서비스 실행
python -m app.server 
```

## Langfuse 설치

참고 : [Langfuse 공식](https://langfuse.com/docs/deployment/local)

```bash
# Clone the Langfuse repository
git clone https://github.com/langfuse/langfuse.git
cd langfuse

# Start the server and database
docker compose up -d
```

### Prompt Template Migration
- 작성 필요


<br/>

## 3.3 PostgreSQL 설정
Langfuse를 사용하기 위해서는 기본적으로 postgresql이 필요하며 설치를 해야한다.
여기서 Langfuse와 함께 설치된 postgresql을 사용하는 것을 기준으로 가이드 한다.
<br/>

### 3.3.1 기존 postgresql에 사용자 추가

먼저 **psql**로 postgresql에 로그인한다.

아래 명령어로 사용자 추가

```sql
CREATE USER ragserver WITH PASSWORD 'ragserver' SUPERUSER;
CREATE DATABASE ragserver owner ragserver;
```

<br/>

### 3.3.2 계정 정보 셋팅

db_model/database.py 아래 정보를 수정한다.

```python
SQLALCHEMY_DATABASE_URL = "postgresql://ragserver:ragserver@rag_server-db-1:5432/ragserver"
```

> **Tip:** 테이블 정보는 database_models.py에 정의 되어 있고, 서비스 실행시 생성된다. (ORM)
> <br/>

## 3.4 SQLAlchemy - 테이블 변경사항 적용하기

Python SQLAlchemy를 사용하여 테이블을 생성한 후, 모델 클래스를 업데이트했을 때 테이블 스키마를 자동으로 변경하려면 **마이그레이션 도구**가 필요. 여기서는 가장 널리 사용되는 마이그레이션 도구 **Alembic**을 사용한다.

Alembic은 SQLAlchemy와 연동되어 데이터베이스 스키마를 관리하고, 모델 클래스 변경에 따라 테이블을 업데이트할 수 있다. Alembic을 사용하면 테이블 스키마를 관리하면서 안전하게 마이그레이션을 적용할 수 있다.

<br/>

### 3.4.1 Alembic 설치

```bash
pip install alembic
```

<br/>

### 3.4.2 Alembic 설정

프로젝트에서 Alembic을 설정하려면, 프로젝트의 루트 디렉토리에서 아래 명령어를 실행하여 초기화.

```bash
alembic init alembic
```

이 명령어는 `alembic/` 디렉토리와 설정 파일인 `alembic.ini`를 생성합니다.

<br/>

### 3.4.3 Alembic 설정 파일 수정

`alembic.ini` 파일에서 데이터베이스 연결 문자열을 설정해야 합니다. 다음과 같이 `sqlalchemy.url` 항목을 찾아 설정

```ini
# alembic.ini 파일
sqlalchemy.url = postgresql://ragserver:ragserver@rag_server-db-1:5432/ragserver
```

<br/>

### 3.4.4 `env.py`에서 SQLAlchemy 모델 연결

`alembic/env.py` 파일을 수정하여 SQLAlchemy 모델을 Alembic에서 인식할 수 있도록 해야 한다. 다음과 같이 `env.py` 파일에서 `target_metadata`를 설정.

```python
from app.db_model.database_models import Base
#... 중간 소스 생략 ...
target_metadata = Base.metadata
```

<br/>

### 3.4.5 마이그레이션 생성

다음 명령어를 사용하여 모델 클래스를 기준으로 자동으로 마이그레이션 파일을 생성

```bash
alembic revision --autogenerate -m "Add last_modified_time to org_resrc"
```

<br/>

### 3.4.6 마이그레이션 파일 검토

`alembic/versions/` 디렉토리에 생성된 마이그레이션 파일을 열어 필요한 변경 사항이 제대로 반영되었는지 확인 할 수 있다.

```python
# 예제
def upgrade():
    op.add_column('org_resrc', sa.Column('last_modified_time', sa.TIMESTAMP(), nullable=True))

def downgrade():
    op.drop_column('org_resrc', 'last_modified_time')
```

<br/>

### 3.4.7 마이그레이션 적용

이제 다음 명령어로 마이그레이션을 데이터베이스에 적용할 수 있다

```bash
# 이 명령어는 가장 최신의 마이그레이션 파일을 기준으로 데이터베이스 스키마를 업데이트한다.
alembic upgrade head
```

<br/>

### 3.4.8 요약

1. **Alembic 설치 및 초기화**: `alembic init` 명령어로 Alembic을 초기화.
2. **데이터베이스 연결 설정**: `alembic.ini` 파일에서 데이터베이스 연결을 설정.
3. **모델 메타데이터 연결**: `alembic/env.py` 파일에서 SQLAlchemy 모델의 메타데이터를 설정.
4. **마이그레이션 생성**: `alembic revision --autogenerate` 명령어로 모델 변경 사항을 반영하는 마이그레이션 파일을 생성.
5. **마이그레이션 적용**: `alembic upgrade head` 명령어로 데이터베이스 스키마를 업데이트.

<br/>

## 3.5 ElasticSearch 설치

`docker run -d --name elasticsearch -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" -e "xpack.security.enabled=false" elasticsearch:8.8.0`

<br/>

# 4. 환경변수

.env 참조

<br/>

# 5. Conda 환경을 옮기는 방법 (이제 사용하지 않음)

1. 현재 환경 내보내기:

   ```
   conda env export > environment.yml
   ```

2. 환경에 설치된 패키지 다운로드:

   ```
   conda list --explicit > spec-file.txt
   mkdir conda_pkgs
   conda pack -n your_env_name -o conda_pkgs/your_env_name.tar.gz
   ```

3. 파일 전송:
   `environment.yml`, `spec-file.txt`, `conda_pkgs` 폴더를 새 PC로 옮깁니다.

4. 새 PC에서 환경 생성:

   ```
   conda create --name new_env --file spec-file.txt
   conda activate new_env
   ```

5. 패키지 설치:
   ```
   conda install --offline -n new_env conda_pkgs/*.tar.bz2
   ```

<br/>

# 6. 실행하기

## 6.1 도커 빌드 하기

```bash
docker build -t rag_server:latest .
```

<br/>

## 6.2 랭퓨즈를 기존의 네트워크에서 분리하기

```bash
docker network disconnect langfuse-main_default langfuse-main-langfuse-server-1
docker network disconnect langfuse-main_default langfuse-main-db-1
```

<br/>

## 6.3 docker-compose.yml로 신규 네트워크 생성 및 컨테이너 네트워크 묶기

docker-compose.yml 필요

```bash
docker-compose up -d
```

<br/>

## 6.4 도커 실행

```bash
docker run -it -p 8000:8000 -p 11434:11434 -v $(pwd):/app/rag_server --network langfuse-main_default --name rag_server rag_server
```

<br/>

## 6.5 도커 터미널에서 실행

```bash
python3.12 -m venv venv # python3.12 -m venv venv
source venv/bin/activate # source venv/bin/activate
pip install -r requirements.txt
```

<br/>

## 6.6 rag server 실행

```bash
python -m app.server

> 개발용 Https로 실행할려면 openssl로 인증서 생성후 rag server 실행
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
python -m app.server --cert-file cert.pem --key-file key.pem

```

<br/>

# 7. 도커 배포하기

## 7.1 도커 컨테이너 이미지로 커밋하기

```bash
docker commit -m "first Creating a snapshot of rag_server" da42eacd1254 rag_server_dev:latest
```

<br/>

## 7.2 도커 저장하기

```bash
docker save -o rag_server_dev.tar rag_server_dev:latest
```

<br/>

## 7.3 도커 이미지 로드하기 (먼저 파일을 옮겨놓고 실행해야 함)

```bash
docker load -i rag_server_dev.tar
```

<br/>

## 7.4 로드된 이미지 확인

```bash
docker images
```

<br/>

## 7.5 로드된 도커 이미지 실행

```bash
docker run -it -p 8000:8000 -p 11434:11434 -v $(pwd):/app/rag_server -v /Users/passion1014/project/langchain/rag_data:/app/rag_data --network rag_server_alfred_network --name rag_server rag_server
```

<br/>

## 7.6 도커 컴포즈

```bash
docker compose down
docker compose up -d
```

<br/>

## 7.7 참고: 도커 명령어 (네트워크)

```bash
docker network ls
docker network inspect rag_server_alfred_network
docker network connect rag_server_alfred_network nervous_poitras
```

<br/>

# 8. Ollama 포트 설정 (window에서는 cmd에서 해야 한다. **powershell 안됨**)

```bash
set OLLAMA_HOST=0.0.0.0
ollama serve
```

<br/>

# 9. Elasticsearch 관련

**하단의 설정 내용은 재정리가 필요함. SSL 설정 필요없어보임**

## 9.1 키바나 설정 (키바나 도커에서 실행)

host를 localhost로 변경

```bash
sed -i 's/0.0.0.0/localhost/g' config/kibana.yml
```

## 9.2 Elasticsearch 서비스 / 키바나 접속

### 9.2.1. 한글처리 플러그인 'nori' 설치 (elasticsearch docker 환경에서 실행)

$ bin/elasticsearch-plugin install analysis-nori

### 9.2.2. 토큰생성

$ elasticsearch-create-enrollment-token -s kibana
eyJ2ZXIiOiI4LjguMCIsImFkciI6WyIxNzIuMTguMC41OjkyMDAiXSwiZmdyIjoiZjJiOWFjZDRlNTI2YWYwMWVmOTk5YjEyYTI4YjRhNzRmYWUzNmUyNzI2YjMyY2M0MzUzMGQxY2MwOTNhODFmNiIsImtleSI6IlAyYXBoWk1CU0I2NXFJXzlTVzlzOmZLMW9SVk1sUmVDWVktaFhlVGQ0aEEifQ==

### 9.2.3. http접속 패스워드 생성

$ elasticsearch-reset-password -u elastic

### 9.2.4. 키바나 접속

http://localhost:5601/

### 9.2.5. 1번에서 생성한 enrollment token 입력

### 9.2.6. Verification 번호 입력

키바나 도커의 Log탭에서 코드값 나옴

### 9.2.7. 계정입력

username=elastic
password=2번에서 생성된 패스워드
<br/>

### 9.2.8 Elasticsearch 전체 내용 조회 URL

curl -X GET "http://localhost:9200/[인덱스명]/\_search?pretty" -H "Content-Type: application/json" -d '
{
"query": {
"match_all": {}
},
"size": 1000
}'
<br/>

# 10. 작업 히스토리

<br/>

## 변경파일 카피하기

./copy_changed_files.sh 파일에서 아래 내용을 수정

- BASE_COMMIT="c78aa6e" # 기준 커밋 (현재는 바로 직전 커밋)
- CURRENT_COMMIT="3a227f2" # 현재 커밋

실행

```bash
$ ./copy_changed_files.sh
```

<br/>

### 2024-11-14 배포본 (SHA)

cc8312ca0662a1fc9c188655daba20ea02350f9c
<br/>

# 11. 모델 관련

<br/>

### 2024-11-14

ollama pull qwen2.5
ollama pull gemma2
ollama pull gemma2:27b
ollama pull mistral-nemo
ollama pull bge-m3

pip install --upgrade langchain-community
pip install --upgrade langchain
pip install --upgrade langgraph
pip install --upgrade pydantic


---
/backend/.start.sh

