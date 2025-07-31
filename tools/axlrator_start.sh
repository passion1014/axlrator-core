#!/bin/bash
#!/bin/bash

LOG_DIR=~/log
mkdir -p "$LOG_DIR"

# 공통 함수: 포트 사용 여부 확인
is_port_in_use() {
    lsof -i tcp:$1 > /dev/null
}

# --- 1. RAG Server (port 8000) ---
if is_port_in_use 8000; then
    echo "[RAG] Already running on port 8000. Skipping..."
else
    echo "[RAG] Starting..."
    cd ~/axlrator-core || exit
    source venv/bin/activate
    nohup python -m axlrator_core.server > "$LOG_DIR/axlrator-core_$(date +'%Y%m%d_%H%M%S').log" 2>&1 &
fi

# --- 2. Backend (port 8080) ---
if is_port_in_use 8080; then
    echo "[Backend] Already running on port 8080. Skipping..."
else
    echo "[Backend] Starting..."
    cd ~/axlrator-webui/backend || exit
    source venv/bin/activate
    nohup ./start.sh > "$LOG_DIR/backend_$(date +'%Y%m%d_%H%M%S').log" 2>&1 &
fi

# --- 3. Frontend (port 4173) ---
if is_port_in_use 4173; then
    echo "[Frontend] Already running on port 4173. Skipping..."
else
    echo "[Frontend] Starting..."
    cd ~/axlrator-webui/frontend || exit
    nohup npm run preview -- --host 0.0.0.0 > "$LOG_DIR/frontend_$(date +'%Y%m%d_%H%M%S').log" 2>&1 &
fi
