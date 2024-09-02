# 건설공제를 위한 LangServe With FastAPI

## 사용 기술 Stack

**LangChain = RAG 서비스 구축을 위한 AI Framework**

**Langfuse = 실행 로그 저장**

**FastAPI = 웹서버**

**SQLAlchemy = ORM 모듈 ( postgresql에 데이터 관리)**


## 실행방법

### 일반 서비스 실행
> python -m app.server

### vs code debugger 실행 
> 디버깅 툴에서 "서버 실행(rag_server)" 메뉴 선택 후 실행



## 설정방법

### 필요한 라이브러리 설치

1) 

참고 파일 : requirements.txt

### Langfuse 설치

참고 : [Langfuse 공식](https://langfuse.com/docs/deployment/local)
```bash
# Clone the Langfuse repository
git clone https://github.com/langfuse/langfuse.git
cd langfuse
 
# Start the server and database
docker compose up
```


### RDB 설정

Langfuse를 사용하기 위해서는 기본적으로 postgresql이 필요하며 설치를 해야한다.<br>
여기서 설치된 postgresql을 사용하는 것을 기준으로 가이드 한다. <br>

#### 1. 기존 postgresql에 사용자 추가
먼저 **psql**로 postgresql에 로그인한다.

아래 명령어로 사용자 추가
```sql
CREATE USER ragserver WITH PASSWORD 'ragserver' SUPERUSER;
CREATE DATABASE ragserver owner ragserver;
```



#### 2. 계정 정보 셋팅
db_model/database.py 아래 정보를 수정한다.
```python
SQLALCHEMY_DATABASE_URL = "postgresql://ragserver:ragserver@localhost/ragserver"

```
>**Tip:** 테이블 정보는 database_models.py에 정의 되어 있고, 서비스 실행시 생성된다. (ORM)

<br><br><br><br><br><br><br><br>
## Procfile

app 패키지(폴더) 하위의 [s](http://server.py)erver.py 안에 app 으로 진입점 초기화 한다는 뜻

![Untitled](images/0.png)

```bash
web: uvicorn app.server:app --host=0.0.0.0 --port=${PORT:-5000}
```

## 프로젝트 설정

1. requirements.txt 생성
    - poetry 사용시 
    
    ```bash
    poetry export -f requirements.txt --output requirements.txt --without-hashes
    ```
    
2. Procfile 생성
   - Procfile 생성 후 아래 내용을 기입
    
    ```bash
    web: uvicorn app.server:app --host=0.0.0.0 --port=${PORT:-5000}
    ```
    
3. git init
    - github 에 소스코드 업로드

## 환경변수

.env 참조



# 실행하기

### 도커 빌드 하기
(개발서버가 linux/arm64/v3 플랫폼으로 되어 있어서 플랫폼을 지정하여 빌드함)
docker buildx build --platform linux/arm64/v3 -t rag_server:latest .

### 도커 실행
docker run -it -p 8000:8000 -p 11434:11434 -v $(pwd):/app/rag_server --network langfuse-main_default --name rag_server rag_server

### 도커 터미널에서 실행
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

### rag server 실행
python -m app.server

### 도커 명령어 (네트워크)
docker network inspect langfuse-main_default
docker network connect langfuse-main_default nervous_poitras

## 도커 배포하기

### 1. 도커 컨테이너 이미지로 커밋하기
docker commit -m "first Creating a snapshot of rag_server" da42eacd1254 rag_server_dev:latest

### 2. 도커 저장하기
docker save -o rag_server_dev.tar rag_server_dev:latest

### 3. 도커 이미지 로드하기  (먼저 파일을 옮겨놓고 실행해야 함)
docker load -i rag_server_dev.tar

### 4. 로드된 이미지 확인
docker images

### 5. 로드된 도커 이미지 실행
docker run -it -p 8000:8000 -p 11434:11434 -v $(pwd):/app/rag_server --network langfuse-main_default --name rag_server rag_server_dev
