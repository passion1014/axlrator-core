# 기본 이미지로 Ubuntu 사용
FROM --platform=linux/arm64/v3 ubuntu:20.04

# 시스템 의존성 설치
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    nodejs \
    npm \
    libpq-dev \
    gcc \
    libffi-dev \
    python3-dev \
    swig \
    libxml2-dev \
    libxslt-dev \
    make \
    git && \
    vim && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# python 및 pip에 대한 심볼릭 링크 생성
RUN ln -sf /usr/bin/python3 /usr/bin/python && \
    ln -sf /usr/bin/pip3 /usr/bin/pip

# 작업 디렉토리 설정
WORKDIR /app/rag_server

# 현재 디렉토리의 모든 파일을 컨테이너의 /app/rag_server 디렉토리에 복사
COPY . /app/rag_server


# ------------------------------------------------------------
# 아래 단계를 이미지 생성할때는 하지 않고 그냥 넘어간다.
# 이후에 컨터이너를 실행시키고 난 후 pip install을 진행한다.
# ------------------------------------------------------------

# 가상 환경 생성 (Python 3을 명시적으로 사용)
# RUN python3 -m venv venv

# requirements.txt 파일 복사 및 가상 환경에서 파이썬 의존성 설치
# COPY requirements.txt /app/rag_server/
# RUN /app/rag_server/venv/bin/python3 -m pip install --no-cache-dir -r /app/rag_server/requirements.txt

# 가상 환경에서 앱 실행
# CMD ["/app/rag_server/venv/bin/python3", "-m", "app.server"]


