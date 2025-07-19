DATE=$(date + "%Y%m%d_%H%M%S")

mkdir -p /log

source /app/axlrator-core/server/bin/activate
nohup python3 -m axlrator_core.server > /log/server_$DATE.log 2>&1 &
tail -f /log/server_$DATE.log