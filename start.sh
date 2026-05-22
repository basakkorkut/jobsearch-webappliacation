#!/bin/bash
BASE="/Users/basakkorkut/Desktop/jobsearchfinal/backend"

echo "Mevcut servisler durduruluyor..."
kill $(lsof -ti :8000 :8001 :8002 :8003) 2>/dev/null
sleep 2

echo "Servisler başlatılıyor..."

nohup "$BASE/api-gateway/.venv/bin/uvicorn" app.main:app --port 8000 --app-dir "$BASE/api-gateway" > /tmp/gateway.log 2>&1 &
nohup "$BASE/job-service/.venv/bin/uvicorn" app.main:app --port 8001 --app-dir "$BASE/job-service" > /tmp/job-service.log 2>&1 &
nohup "$BASE/notification-service/.venv/bin/uvicorn" app.main:app --port 8002 --app-dir "$BASE/notification-service" > /tmp/notification.log 2>&1 &
nohup "$BASE/ai-agent-service/.venv/bin/uvicorn" app.main:app --port 8003 --app-dir "$BASE/ai-agent-service" > /tmp/agent.log 2>&1 &

echo "8 saniye bekleniyor..."
sleep 8

echo "=== DURUM ==="
curl -s "http://localhost:8000/api/v1/search?limit=1" | python3 -c "import sys,json;d=json.load(sys.stdin);print('✓ Gateway + Search:', d['total'], 'ilan')" 2>/dev/null || echo "✗ Gateway"
curl -s "http://localhost:8001/health" | python3 -c "import sys,json;d=json.load(sys.stdin);print('✓ Job Service:', d['status'])" 2>/dev/null || echo "✗ Job Service"
curl -s -X POST "http://localhost:8003/api/v1/agent/chat" -H "Content-Type: application/json" -d '{"messages":[{"role":"user","content":"test"}]}' | python3 -c "import sys,json;json.load(sys.stdin);print('✓ AI Agent: OK')" 2>/dev/null || echo "✗ Agent"
echo "Frontend: http://localhost:5173"
