#!/bin/bash
echo "🔴 Tüm servisler durduruluyor..."
lsof -ti :8000,8001,8002,8003,5173 | xargs kill -9 2>/dev/null
echo "✅ Tüm portlar temizlendi (8000, 8001, 8002, 8003, 5173)"
