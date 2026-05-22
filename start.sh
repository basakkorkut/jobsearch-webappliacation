#!/bin/bash
ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "🔴 Eski processler temizleniyor..."
lsof -ti :8000,8001,8002,8003,5173 | xargs kill -9 2>/dev/null
sleep 1

echo "🟡 Job Service başlatılıyor (:8001)..."
cd "$ROOT/backend/job-service"
.venv/bin/uvicorn app.main:app --port 8001 > /tmp/job-service.log 2>&1 &

echo "🟡 Notification Service başlatılıyor (:8002)..."
cd "$ROOT/backend/notification-service"
.venv/bin/uvicorn app.main:app --port 8002 > /tmp/notification.log 2>&1 &

echo "🟡 AI Agent Service başlatılıyor (:8003)..."
cd "$ROOT/backend/ai-agent-service"
.venv/bin/uvicorn app.main:app --port 8003 > /tmp/ai-agent.log 2>&1 &

echo "🟡 API Gateway başlatılıyor (:8000)..."
cd "$ROOT/backend/api-gateway"
.venv/bin/uvicorn app.main:app --port 8000 > /tmp/gateway.log 2>&1 &

echo "🟡 Frontend başlatılıyor (:5173)..."
cd "$ROOT/frontend"
npm run dev -- --port 5173 > /tmp/frontend.log 2>&1 &

echo ""
echo "⏳ Servisler başlıyor (5 saniye bekleniyor)..."
sleep 5

echo ""
echo "=== DURUM ==="
check() {
  if curl -s "$1" > /dev/null 2>&1; then
    echo "  ✅ $2"
  else
    echo "  ❌ $2 — log: $3"
  fi
}

check "http://localhost:8001/health" "Job Service          :8001" "/tmp/job-service.log"
check "http://localhost:8002/health" "Notification Service :8002" "/tmp/notification.log"
check "http://localhost:8003/health" "AI Agent Service     :8003" "/tmp/ai-agent.log"
check "http://localhost:8000/health" "API Gateway          :8000" "/tmp/gateway.log"
check "http://localhost:5173"        "Frontend             :5173" "/tmp/frontend.log"

echo ""
echo "🌐 Tarayıcıda aç: http://localhost:5173"
echo ""
echo "Logları görmek için:"
echo "  tail -f /tmp/job-service.log"
echo "  tail -f /tmp/ai-agent.log"
echo "  tail -f /tmp/gateway.log"
echo "  tail -f /tmp/frontend.log"
