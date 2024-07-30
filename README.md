# LangServe + Heroku

## Poetry

poetry 설치

```bash
pip install poetry
```

필요한 패키지 추가

```bash
poetry add langchain-openai
```

langserve 실행

```bash
poetry run langchain serve
```

langchain-template 코드 추가

```bash
poetry run langchain app add retrieval-agent
```

langchain-template 코드 제거

```bash
poetry run langchain app remove retrieval-agent
```


## vs-code에서 debugger 실행

./vscode/launch.json 파일 참조



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




# 모듈 설명

### server.py
FastAPI 를 사용한 서버 시작

### chat.py

### chain.py
