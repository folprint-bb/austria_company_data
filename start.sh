#!/bin/bash

echo "🚀 FirmenABC Scraper indítása..."
echo ""

if ! command -v python3 &> /dev/null
then
    echo "❌ Python3 nincs telepítve!"
    exit 1
fi

echo "📦 Függőségek ellenőrzése..."
pip3 install -r requirements.txt

echo ""
echo "✅ Alkalmazás indítása..."
echo "🌐 Nyisd meg a böngészőt: http://localhost:5000"
echo ""

python3 app.py
